from __future__ import annotations
import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


TITLE_ORDER = ["ko", "en", "ja", "zh-cn"]
SOURCE_ORDER = ["ko", "en", "ja", "zh-cn"]


@dataclass
class IndexEntry:
    id: str
    title: Optional[str]
    start: Optional[str]
    end: Optional[str]
    city: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    category: Optional[str]
    isPopup: Optional[bool]
    thumb: Optional[str]
    sourceUrl: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "city": self.city,
            "lat": self.lat,
            "lon": self.lon,
            "category": self.category,
            "isPopup": self.isPopup,
            "thumb": self.thumb,
            "sourceUrl": self.sourceUrl,
        }


def _pick_title(rec: Dict[str, Any]) -> Optional[str]:
    tr = rec.get("translations") or {}
    if not isinstance(tr, dict):
        return None
    for loc in TITLE_ORDER:
        v = tr.get(loc)
        if isinstance(v, dict) and v.get("title"):
            return str(v.get("title"))
    # Fallback: try any title
    for v in tr.values():
        if isinstance(v, dict) and v.get("title"):
            return str(v.get("title"))
    return None


def _pick_source_url(rec: Dict[str, Any]) -> Optional[str]:
    src = rec.get("source") or {}
    if isinstance(src, dict):
        for loc in SOURCE_ORDER:
            key = f"{loc}Url"
            if src.get(key):
                return str(src.get(key))
        # Any value in source
        for v in src.values():
            if isinstance(v, str) and v:
                return v
    # Fallback to first link
    links = rec.get("links") or []
    if isinstance(links, list) and links:
        href = links[0].get("href") if isinstance(links[0], dict) else None
        if href:
            return str(href)
    return None


def _pick_thumb(rec: Dict[str, Any]) -> Optional[str]:
    # Prefer meta.images.selectionRule when available
    imgs_meta = (rec.get("meta") or {}).get("images") or {}
    selection_rule = imgs_meta.get("selectionRule") if isinstance(imgs_meta, dict) else None
    images = rec.get("images") or []
    if not isinstance(images, list) or not images:
        return None

    def by_role(role: str) -> List[Dict[str, Any]]:
        return [img for img in images if isinstance(img, dict) and (img.get("role") or "") == role]

    def best_url(candidates: List[Dict[str, Any]]) -> Optional[str]:
        if not candidates:
            return None
        # Prefer small_square variant, else full, else first
        sq = next((i for i in candidates if i.get("variant") == "small_square" and i.get("url")), None)
        if sq:
            return str(sq.get("url"))
        full = next((i for i in candidates if i.get("variant") == "full" and i.get("url")), None)
        if full:
            return str(full.get("url"))
        first = next((i for i in candidates if i.get("url")), None)
        return str(first.get("url")) if first else None

    if selection_rule == "headImage":
        url = best_url(by_role("head"))
        if url:
            return url
    elif selection_rule == "firstContentImage":
        content = [img for img in images if (img.get("role") or "") != "head"]
        url = best_url(content)
        if url:
            return url

    # Generic fallback: try head then any
    url = best_url(by_role("head"))
    if url:
        return url
    return best_url(images)


def _safe_get(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def record_to_index_entry(rec: Dict[str, Any]) -> Optional[IndexEntry]:
    rid = rec.get("id")
    if not rid:
        return None
    duration = rec.get("duration") or {}
    address = rec.get("address") or {}
    geo = rec.get("geo") or {}
    return IndexEntry(
        id=str(rid),
        title=_pick_title(rec),
        start=duration.get("start"),
        end=duration.get("end"),
        city=address.get("city"),
        lat=geo.get("lat"),
        lon=geo.get("lon"),
        category=rec.get("category"),
        isPopup=rec.get("isPopup"),
        thumb=_pick_thumb(rec),
        sourceUrl=_pick_source_url(rec),
    )


def load_records(input_dir: Path) -> Iterable[Dict[str, Any]]:
    for p in sorted(input_dir.glob("*.json")):
        try:
            yield json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue


def write_json(path: Path, data: Any) -> int:
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def shard_monthly(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for e in entries:
        # prefer start month, else end, else unknown
        key_src = e.get("start") or e.get("end")
        month = "unknown"
        if isinstance(key_src, str) and len(key_src) >= 7:
            month = key_src[:7]  # YYYY-MM
        buckets.setdefault(month, []).append(e)
    return buckets


def build_index(
    input_dir: Path,
    output: Path,
    max_bytes: int,
    shard: str,
) -> Tuple[str, Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for rec in load_records(input_dir):
        ent = record_to_index_entry(rec)
        if ent is None:
            continue
        entries.append(ent.to_dict())

    manifest: Dict[str, Any] = {
        "generatedAt": datetime.utcnow().isoformat(),
        "total": len(entries),
        "mode": "single",
        "version": 1,
    }

    if shard == "monthly":
        buckets = shard_monthly(entries)
        months = sorted(buckets.keys())
        out_dir = output.parent
        for m in months:
            fname = f"index-{m}.json" if m != "unknown" else "index-unknown.json"
            write_json(out_dir / fname, buckets[m])
        manifest.update({"mode": "monthly", "months": months})
        # Also write a thin top-level index.json with empty array to keep paths stable
        write_json(output, [])
        return "monthly", manifest

    # single file mode by default
    size = write_json(output, entries)
    if size > max_bytes:
        # Fallback to monthly sharding automatically
        buckets = shard_monthly(entries)
        months = sorted(buckets.keys())
        out_dir = output.parent
        for m in months:
            fname = f"index-{m}.json" if m != "unknown" else "index-unknown.json"
            write_json(out_dir / fname, buckets[m])
        manifest.update({
            "mode": "monthly",
            "months": months,
            "note": f"single exceeded {max_bytes} bytes; sharded",
        })
        # Replace main with empty array placeholder
        write_json(output, [])
        return "monthly", manifest

    return "single", manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build lightweight index for popup records")
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(Path("data") / "popups"),
        help="Directory containing per-record JSON files",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path("data") / "index.json"),
        help="Path to write combined index JSON",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=5 * 1024 * 1024,
        help="Max size for single index.json before sharding",
    )
    parser.add_argument(
        "--shard",
        type=str,
        choices=["none", "monthly"],
        default="none",
        help="Force sharding strategy (none=auto)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output = Path(args.output)
    shard_mode = args.shard
    if shard_mode == "none":
        shard_mode = "single"

    mode, manifest = build_index(
        input_dir=input_dir,
        output=output,
        max_bytes=int(args.max_bytes),
        shard="monthly" if shard_mode == "monthly" else "single",
    )

    manifest_path = output.parent / "index-manifest.json"
    write_json(manifest_path, manifest)
    print(f"Index build complete: mode={mode}, total={manifest['total']}, out={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

