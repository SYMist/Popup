from __future__ import annotations

import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import requests
from tqdm import tqdm

from scripts.rules import PopupRules
from scripts.triple_client import (
    SITEMAP_INDEX_URL,
    extract_id_from_url,
    fetch,
    fetch_festa_by_lang,
    parse_sitemap_index,
    parse_sitemap_urls,
)
from scripts.storage import save_record_json, upsert_records_sqlite


LANGS = ["ko", "en", "ja"]


def load_sitemap_festa_urls(session: requests.Session) -> List[str]:
    idx = fetch(session, SITEMAP_INDEX_URL).text
    all_sitemaps = [u for u in parse_sitemap_index(idx) if "sitemap-festa-detail-urls-" in u]
    urls: List[str] = []
    for sm in tqdm(all_sitemaps, desc="Fetch sitemaps"):
        try:
            xml = fetch(session, sm).text
            urls.extend(parse_sitemap_urls(xml))
            time.sleep(0.4)
        except Exception:
            continue
    return urls


def classify_popup(rules: PopupRules, record: Dict[str, Any]) -> Dict[str, Any]:
    cat = (record.get("category") or "").upper()
    titles = []
    for loc in LANGS:
        t = record.get("translations", {}).get(loc, {}).get("title")
        if t:
            titles.append(t)
    start = record.get("duration", {}).get("start")
    end = record.get("duration", {}).get("end")
    from datetime import date

    sdt = date.fromisoformat(start) if start else None
    edt = date.fromisoformat(end) if end else None

    matched = rules.match_category(cat) or rules.match_keywords(titles) or rules.match_duration(sdt, edt)
    record.setdefault("meta", {})["detection"] = {
        "rule": "category|keyword|duration",
        "category": rules.match_category(cat),
        "keyword": rules.match_keywords(titles),
        "duration": rules.match_duration(sdt, edt),
    }
    record["isPopup"] = bool(matched)
    return record


def merge_localized(base: Dict[str, Any], festa: Dict[str, Any], lang: str) -> Dict[str, Any]:
    # Core fields (first-seen wins; use ko as baseline typically)
    base.setdefault("id", festa.get("resourceId"))
    base.setdefault("category", festa.get("category"))
    # duration/address/geo/pricing from any locale if missing
    base.setdefault("duration", festa.get("duration") or {})
    base.setdefault("address", festa.get("address") or {})
    base.setdefault("geo", festa.get("geolocation") or {})
    base.setdefault("pricing", festa.get("pricing") or {})

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


def main(max_items: Optional[int] = None) -> int:
    rules = PopupRules()
    session = requests.Session()

    festa_urls = load_sitemap_festa_urls(session)
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

    if max_items:
        ordered_ids = ordered_ids[:max_items]

    records: List[Dict[str, Any]] = []
    saved = 0
    skipped = 0

    for fid in tqdm(ordered_ids, desc="Fetch festas"):
        merged: Dict[str, Any] = {}
        any_lang_ok = False
        for lang in LANGS:
            try:
                festa = fetch_festa_by_lang(session, fid, lang)
                if festa:
                    any_lang_ok = True
                    merged = merge_localized(merged, festa, lang)
            except Exception:
                continue
        if not any_lang_ok:
            skipped += 1
            continue

        # classify popup and filter
        merged = classify_popup(rules, merged)
        if not merged.get("isPopup"):
            skipped += 1
            continue

        # Meta info
        merged.setdefault("meta", {})["fetchedAt"] = datetime.utcnow().isoformat()

        # Save JSON and collect for DB
        save_record_json(merged)
        records.append(merged)
        saved += 1

    # Update SQLite from collected records
    if records:
        upsert_records_sqlite(records)

    print(f"Saved: {saved}, Skipped(non-popup or failed): {skipped}")
    return 0


if __name__ == "__main__":
    max_items = None
    if len(sys.argv) > 1:
        try:
            max_items = int(sys.argv[1])
        except Exception:
            max_items = None
    raise SystemExit(main(max_items))
