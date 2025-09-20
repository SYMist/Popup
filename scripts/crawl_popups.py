from __future__ import annotations
import sys
import time
from datetime import datetime, date
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json

import requests
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.triple_client import (
    SITEMAP_INDEX_URL,
    extract_id_from_url,
    fetch,
    fetch_festa_by_lang,
    parse_sitemap_index,
    parse_sitemap_urls,
)
from scripts.storage import save_record_json, upsert_records_sqlite
from scripts.rules import PopupRules, load_rules
from scripts.http_cache import HttpCache
from scripts.validators import validate_record


# Preferred locales to fetch (ko often missing; include zh-CN)
LANGS = ["zh-cn", "en", "ja", "ko"]


class RateLimiter:
    def __init__(self, qps: float) -> None:
        self.interval = 1.0 / qps if qps and qps > 0 else 0.0
        self._lock = threading.Lock()
        self._next_at = 0.0

    def acquire(self) -> None:
        if self.interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            sleep_for = self._next_at - now
            if sleep_for > 0:
                # Reserve slot first to reduce thundering herd
                self._next_at += self.interval
            else:
                self._next_at = now + self.interval
        if sleep_for > 0:
            time.sleep(sleep_for)


def load_sitemap_festa_urls(session: requests.Session, limiter: Optional[RateLimiter] = None) -> List[str]:
    if limiter:
        limiter.acquire()
    idx = fetch(session, SITEMAP_INDEX_URL).text
    all_sitemaps = [u for u in parse_sitemap_index(idx) if "sitemap-festa-detail-urls-" in u]
    urls: List[str] = []
    for sm in tqdm(all_sitemaps, desc="Fetch sitemaps"):
        try:
            if limiter:
                limiter.acquire()
            xml = fetch(session, sm).text
            urls.extend(parse_sitemap_urls(xml))
        except Exception:
            continue
    return urls


def _non_empty(val: Any) -> bool:
    return val not in (None, "", [], {})


def _merge_nested_fields(dst: Dict[str, Any], src: Dict[str, Any], key: str) -> None:
    if not isinstance(src, dict):
        return
    cur = dst.setdefault(key, {}) if isinstance(dst.get(key), dict) else dst.setdefault(key, {})
    for k, v in src.items():
        # Only overwrite when destination missing/empty and source has a value
        if _non_empty(v) and not _non_empty(cur.get(k)):
            cur[k] = v


def merge_localized(base: Dict[str, Any], festa: Dict[str, Any], lang: str) -> Dict[str, Any]:
    # Core fields (first-seen wins; use ko as baseline typically)
    base.setdefault("id", festa.get("resourceId"))
    base.setdefault("category", festa.get("category"))
    # duration/address/geo/pricing: prefer to fill empty subfields from any locale
    _merge_nested_fields(base, festa.get("duration") or {}, "duration")
    _merge_nested_fields(base, festa.get("address") or {}, "address")
    _merge_nested_fields(base, festa.get("geolocation") or {}, "geo")
    _merge_nested_fields(base, festa.get("pricing") or {}, "pricing")

    # links (merge unique by href)
    base_links = base.setdefault("links", [])
    hrefs = {l.get("href") for l in base_links}
    for l in festa.get("links", []) or []:
        href = l.get("href")
        if href and href not in hrefs:
            base_links.append(l)
            hrefs.add(href)

    # images (dedup by URL)
    base_imgs = base.setdefault("images", [])
    seen = {img.get("url") for img in base_imgs}
    for img in festa.get("images", []) or []:
        url = img.get("url")
        if url and url not in seen:
            base_imgs.append(img)
            seen.add(url)

    # translations per locale
    tr = base.setdefault("translations", {})
    tloc = tr.setdefault(lang, {})
    if festa.get("title"):
        tloc["title"] = festa.get("title")
    # address string fallback construction
    addr = festa.get("address") or {}
    if addr.get("city") or addr.get("street"):
        tloc["address"] = ", ".join([x for x in [addr.get("city"), addr.get("street")] if x])
    # price description
    pricing = festa.get("pricing") or {}
    if pricing.get("description"):
        tloc["priceDesc"] = pricing.get("description")

    # source urls per locale
    src = base.setdefault("source", {})
    url_key = f"{lang}Url"
    if festa.get("_sourceUrl"):
        src[url_key] = festa.get("_sourceUrl")

    return base


def main(limit: Optional[int], fast: bool, workers: int, qps: float, langs: List[str]) -> int:
    session = requests.Session()
    limiter = RateLimiter(qps) if qps and qps > 0 else None
    cache = HttpCache()

    festa_urls = load_sitemap_festa_urls(session, limiter)
    festa_ids: List[str] = []
    for u in festa_urls:
        fid = extract_id_from_url(u)
        if fid:
            festa_ids.append(fid)
    # Uniq preserving order
    seen: Set[str] = set()
    ordered_ids: List[str] = []
    for fid in festa_ids:
        if fid not in seen:
            seen.add(fid)
            ordered_ids.append(fid)

    if limit:
        ordered_ids = ordered_ids[:limit]

    errors: List[Dict[str, Any]] = []
    err_lock = threading.Lock()

    def process_one(fid: str) -> Optional[Dict[str, Any]]:
        sess = requests.Session()
        merged: Dict[str, Any] = {}
        any_lang_ok = False
        for lang in langs:
            try:
                festa = fetch_festa_by_lang(sess, fid, lang, limiter.acquire if limiter else None, cache)
                if festa:
                    any_lang_ok = True
                    merged = merge_localized(merged, festa, lang)
                    if fast:
                        break
            except Exception as e:
                with err_lock:
                    errors.append({"id": fid, "lang": lang, "error": repr(e)})
                continue
        if not any_lang_ok:
            return None
        merged.setdefault("meta", {})["fetchedAt"] = datetime.utcnow().isoformat()
        # Classification (non-blocking): tag popup detection by category|keyword|duration
        rules = load_rules()
        titles: List[str] = []
        tr = merged.get("translations") or {}
        if isinstance(tr, dict):
            for loc, vals in tr.items():
                if isinstance(vals, dict):
                    t = vals.get("title")
                    if t:
                        titles.append(str(t))
        dur = merged.get("duration") or {}
        start = _parse_date(dur.get("start")) if isinstance(dur, dict) else None
        end = _parse_date(dur.get("end")) if isinstance(dur, dict) else None
        is_popup, det_details = rules.classify(
            category=merged.get("category"), titles=titles, start=start, end=end
        )
        merged["isPopup"] = is_popup
        if any(det_details.values()):
            merged.setdefault("meta", {})["detection"] = det_details
        # Image selection meta
        imgs = merged.get("images") or []
        if isinstance(imgs, list):
            merged.setdefault("meta", {})["images"] = _compute_image_meta(imgs)
        # Pricing normalization from description texts
        price_texts: List[str] = []
        pr = merged.get("pricing") or {}
        if isinstance(pr, dict) and pr.get("description"):
            price_texts.append(str(pr.get("description")))
        if isinstance(tr, dict):
            for loc, vals in tr.items():
                if isinstance(vals, dict) and vals.get("priceDesc"):
                    price_texts.append(str(vals.get("priceDesc")))
        norm = _normalize_pricing_from_texts(price_texts)
        if norm:
            merged.setdefault("pricing", {})["normalized"] = norm
        # Validation (non-blocking): attach errors/warnings
        errs, warns = validate_record(merged)
        if errs or warns:
            merged.setdefault("meta", {}).setdefault("validation", {})["errors"] = errs
            merged.setdefault("meta", {}).setdefault("validation", {})["warnings"] = warns
        save_record_json(merged)
        return merged

    records: List[Dict[str, Any]] = []
    saved = 0
    skipped = 0

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for res in tqdm(ex.map(process_one, ordered_ids), total=len(ordered_ids), desc="Fetch festas"):
            if res:
                records.append(res)
                saved += 1
            else:
                skipped += 1

    # Update SQLite from collected records
    if records:
        upsert_records_sqlite(records)

    # Retry queue for failures (second attempt, sequential)
    if errors:
        retry_ids = sorted({e["id"] for e in errors})
        retry_saved = 0
        for fid in tqdm(retry_ids, desc="Retry failures"):
            try:
                res = process_one(fid)
                if res:
                    retry_saved += 1
            except Exception:
                pass
        if retry_saved:
            print(f"Retry saved additionally: {retry_saved}")

    # Emit report
    report = {
        "saved": saved,
        "skipped": skipped,
        "failedEntries": errors,
    }
    try:
        Path("data").mkdir(parents=True, exist_ok=True)
        (Path("data") / "crawl_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass

    print(f"Saved: {saved}, Skipped(non-popup/failed/unchanged): {skipped}, Failures: {len(errors)}")
    return 0


 
def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _compute_image_meta(images: List[Dict[str, Any]]) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"total": len(images), "gallery": max(0, len(images) - 1)}
    if images:
        first = images[0]
        role = first.get("role") or ""
        if role == "head":
            meta["selectionRule"] = "headImage"
        else:
            meta["selectionRule"] = "firstContentImage"
        meta["representativeRole"] = role or "unknown"
    return meta


_CURRENCY_MAP = [
    ("₩", "KRW"), ("원", "KRW"), ("KRW", "KRW"), ("WON", "KRW"),
    ("$", "USD"), ("USD", "USD"), ("달러", "USD"),
    ("¥", "JPY"), ("JPY", "JPY"), ("엔", "JPY"), ("円", "JPY"),
    ("CNY", "CNY"), ("RMB", "CNY"), ("人民币", "CNY"), ("元", "CNY"), ("￥", "CNY"), ("CN¥", "CNY"),
]


def _normalize_amount_token(tok: str) -> Optional[float]:
    try:
        t = tok.replace(",", "").replace(" ", "")
        return float(t)
    except Exception:
        return None


def _normalize_pricing_from_texts(texts: List[str]) -> Optional[Dict[str, Any]]:
    if not texts:
        return None
    import re as _re
    # Detect currency
    currency = None
    joined = " \n ".join(texts)
    for pat, code in _CURRENCY_MAP:
        if pat.lower() in joined.lower():
            currency = code
            break
    # Extract numbers
    nums: List[float] = []
    for txt in texts:
        for m in _re.finditer(r"(?<!\d)(\d{1,3}(?:[ ,]\d{3})+|\d+)(?:\.\d+)?", txt):
            val = _normalize_amount_token(m.group(0))
            if val is not None:
                nums.append(val)
    if not nums and currency is None:
        return None
    norm: Dict[str, Any] = {}
    if nums:
        norm["amountMin"] = float(min(nums))
        norm["amountMax"] = float(max(nums))
    if currency:
        norm["currency"] = currency
    return norm if norm else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl popup festas")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of festa IDs")
    parser.add_argument("--fast", action="store_true", help="Stop after first successful locale")
    parser.add_argument("--workers", type=int, default=8, help="Number of concurrent workers")
    parser.add_argument("--qps", type=float, default=2.0, help="Global requests per second")
    parser.add_argument(
        "--langs",
        type=str,
        default=",".join(LANGS),
        help="Comma-separated locale order to try",
    )
    args = parser.parse_args()
    lang_list = [x.strip() for x in args.langs.split(",") if x.strip()]
    raise SystemExit(main(args.limit, args.fast, args.workers, args.qps, lang_list))
