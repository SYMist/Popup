from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from tenacity import retry, wait_exponential_jitter, stop_after_attempt


SITEMAP_INDEX_URL = "https://triple.global/sitemap-index.xml"


@dataclass
class FestaData:
    id: str
    category: Optional[str]
    title: Optional[str]
    duration_start: Optional[date]
    duration_end: Optional[date]
    lon: Optional[float]
    lat: Optional[float]
    address_city: Optional[str]
    address_street: Optional[str]
    links: List[Dict[str, str]]
    pricing: Dict[str, Any]
    images: List[Dict[str, Any]]


def _lang_headers(lang: str) -> Dict[str, str]:
    return {
        "accept-language": lang,
        "user-agent": "popup-crawler/1.0 (+https://github.com/)",
    }


@retry(wait=wait_exponential_jitter(initial=1, max=10), stop=stop_after_attempt(3))
def fetch(session: requests.Session, url: str, *, headers: Optional[Dict[str, str]] = None) -> requests.Response:
    resp = session.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp


def parse_sitemap_index(xml_text: str) -> List[str]:
    soup = BeautifulSoup(xml_text, "lxml-xml")
    return [loc.get_text(strip=True) for loc in soup.find_all("loc")]


def parse_sitemap_urls(xml_text: str) -> List[str]:
    soup = BeautifulSoup(xml_text, "lxml-xml")
    return [loc.get_text(strip=True) for loc in soup.find_all("loc")]


def extract_id_from_url(url: str) -> Optional[str]:
    m = re.search(r"/festas/([0-9a-f\-]{36})", url)
    return m.group(1) if m else None


def _lang_path(lang: str) -> str:
    # Normalize language code for path segment (lowercase, keep hyphen)
    return lang.lower()


def triple_detail_url(lang: str, festa_id: str) -> str:
    # Interpark Global now serves festa details
    return f"https://interparkglobal.com/{_lang_path(lang)}/festas/{festa_id}"


def parse_next_data(html: str) -> Optional[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    # Try canonical Next.js data
    node = soup.find("script", id="__NEXT_DATA__")
    if node and node.string:
        try:
            return json.loads(node.string)
        except Exception:
            pass
    # Fallback: any script containing apolloState JSON
    for s in soup.find_all("script"):
        txt = s.string or s.text or ""
        if "apolloState" in txt and txt.strip().startswith("{"):
            try:
                return json.loads(txt)
            except Exception:
                continue
    return None


def get_apollo_state(next_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Support both legacy apolloState and Next pageProps __APOLLO_CACHE__
    # 1) Legacy placements
    for path in (
        ["props", "pageProps", "apolloState"],
        ["props", "apolloState"],
        ["apolloState"],
    ):
        cur = next_data
        ok = True
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok and isinstance(cur, dict):
            return cur
    # 2) Interpark Next.js cache
    cur = next_data
    for k in ("props", "pageProps", "__APOLLO_CACHE__"):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            cur = None
            break
    if isinstance(cur, dict):
        return cur
    return None


def deref(apollo: Dict[str, Any], obj: Any) -> Any:
    if isinstance(obj, dict) and "__ref" in obj:
        ref = obj["__ref"]
        return apollo.get(ref, obj)
    return obj


def find_festa_node(apollo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    root = apollo.get("ROOT_QUERY")
    if isinstance(root, dict):
        for k, v in root.items():
            if isinstance(k, str) and "getFesta" in k:
                v = deref(apollo, v)
                if isinstance(v, dict) and v.get("__typename") == "Festa":
                    return v
    # Fallback: search any Festa entity
    for v in apollo.values():
        if isinstance(v, dict) and v.get("__typename") == "Festa":
            return v
    return None


def _read_str(d: Dict[str, Any], key: str) -> Optional[str]:
    x = d.get(key)
    return x if isinstance(x, str) else None


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _number(n: Any) -> Optional[float]:
    try:
        return float(n)
    except Exception:
        return None


def _extract_image_urls(img_obj: Dict[str, Any]) -> List[Tuple[str, str]]:
    urls: List[Tuple[str, str]] = []
    # Support both legacy flat variants and nested sizes
    variant_candidates = ("full", "large", "original", "small", "small_square")
    # 1) Nested under sizes
    sizes = img_obj.get("sizes")
    if isinstance(sizes, dict):
        for variant in variant_candidates:
            v = sizes.get(variant)
            if isinstance(v, dict):
                url = _read_str(v, "url")
                if url:
                    urls.append((variant, url))
    # 2) Flat fields
    for variant in variant_candidates:
        v = img_obj.get(variant)
        if isinstance(v, dict):
            url = _read_str(v, "url")
            if url:
                urls.append((variant, url))
    # 3) Direct url field
    direct = _read_str(img_obj, "url")
    if direct:
        urls.append(("direct", direct))
    return urls


def extract_festa(apollo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    festa = find_festa_node(apollo)
    if not festa:
        return None

    # Resolve fields (with possible refs)
    head_image = deref(apollo, festa.get("headImage", {})) if isinstance(festa, dict) else {}
    contents = festa.get("contents") or []
    images: List[Dict[str, Any]] = []

    # Representative image first
    if isinstance(head_image, dict):
        for variant, url in _extract_image_urls(head_image):
            images.append({"url": url, "variant": variant, "role": "head"})

    # Content images
    if isinstance(contents, list):
        for c in contents:
            if not isinstance(c, dict):
                continue
            img_list = c.get("image") or []
            if not isinstance(img_list, list):
                continue
            for io in img_list:
                if not isinstance(io, dict):
                    continue
                for variant, url in _extract_image_urls(io):
                    images.append({"url": url, "variant": variant, "role": "content"})

    # Deduplicate by URL preserving order
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for img in images:
        url = img.get("url")
        if not url or url in seen:
            continue
        if isinstance(url, str) and url.startswith("//"):
            url = "https:" + url
            img["url"] = url
        if isinstance(url, str) and url.startswith("http"):
            seen.add(url)
            deduped.append(img)

    # Representative + up to 5 gallery images (after representative)
    rep: List[Dict[str, Any]] = []
    gallery: List[Dict[str, Any]] = []
    for img in deduped:
        if not rep and img.get("role") == "head":
            rep.append(img)
        else:
            gallery.append(img)
    if not rep and gallery:
        # If no head image, take first content image as representative
        rep = [gallery.pop(0)]
    gallery = gallery[:5]

    # Links
    links = []
    for l in festa.get("links") or []:
        if not isinstance(l, dict):
            continue
        href = _read_str(l, "href")
        label = _read_str(l, "label")
        if href:
            links.append({"href": href, "label": label or ""})

    # Pricing
    pricing = festa.get("pricing") if isinstance(festa.get("pricing"), dict) else {}

    # Address & Geo
    addr = festa.get("address") if isinstance(festa.get("address"), dict) else {}
    geo = festa.get("geolocation") if isinstance(festa.get("geolocation"), dict) else {}
    coords = geo.get("coordinates") if isinstance(geo.get("coordinates"), list) else []
    lon = _number(coords[0]) if len(coords) >= 1 else None
    lat = _number(coords[1]) if len(coords) >= 2 else None

    return {
        "resourceId": _read_str(festa, "resourceId"),
        "title": _read_str(festa, "title"),
        "category": _read_str(festa, "category"),
        "duration": {
            "start": _read_str(festa.get("duration", {}), "start"),
            "end": _read_str(festa.get("duration", {}), "end"),
        },
        "address": {
            "city": _read_str(addr, "city"),
            "street": _read_str(addr, "street"),
        },
        "geolocation": {"lon": lon, "lat": lat},
        "links": links,
        "pricing": {
            "type": _read_str(pricing, "type"),
            "description": _read_str(pricing, "description"),
        },
        "images": rep + gallery,
    }


def fetch_festa_by_lang(session: requests.Session, festa_id: str, lang: str) -> Optional[Dict[str, Any]]:
    url = triple_detail_url(lang, festa_id)
    resp = fetch(session, url, headers=_lang_headers(lang))
    time.sleep(0.8)  # be polite
    data = parse_next_data(resp.text)
    if not data:
        return None
    apollo = get_apollo_state(data)
    if not apollo:
        return None
    festa = extract_festa(apollo)
    if not festa:
        return None
    festa["_sourceUrl"] = url
    return festa
