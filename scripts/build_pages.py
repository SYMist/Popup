from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple
import datetime as dt


TITLE_ORDER = ["ko", "en", "ja", "zh-cn"]
ADSENSE_PUB = "ca-pub-5716436301710258"
SITE_ORIGIN = "https://popup.deluxo.co.kr"


def _pick_title(rec: Dict[str, Any]) -> Optional[str]:
    tr = rec.get("translations") or {}
    if isinstance(tr, dict):
        for loc in TITLE_ORDER:
            v = tr.get(loc)
            if isinstance(v, dict) and v.get("title"):
                return str(v.get("title"))
        for v in tr.values():
            if isinstance(v, dict) and v.get("title"):
                return str(v.get("title"))
    return None


def _pick_thumb(rec: Dict[str, Any]) -> Optional[str]:
    imgs = rec.get("images") or []
    if not isinstance(imgs, list) or not imgs:
        return None
    # prefer small_square then full
    sq = next((i for i in imgs if i.get("variant") == "small_square" and i.get("url")), None)
    if sq:
        return str(sq.get("url"))
    full = next((i for i in imgs if i.get("variant") == "full" and i.get("url")), None)
    if full:
        return str(full.get("url"))
    first = next((i for i in imgs if i.get("url")), None)
    return str(first.get("url")) if first else None


def _pick_source_url(rec: Dict[str, Any]) -> Optional[str]:
    src = rec.get("source") or {}
    if isinstance(src, dict):
        for loc in ["ko", "en", "ja", "zh-cn"]:
            key = f"{loc}Url"
            if src.get(key):
                return str(src.get(key))
        for v in src.values():
            if isinstance(v, str) and v:
                return v
    links = rec.get("links") or []
    if isinstance(links, list) and links:
        href = links[0].get("href") if isinstance(links[0], dict) else None
        if href:
            return str(href)
    return None


def load_records(input_dir: Path) -> Iterable[Tuple[Dict[str, Any], Path]]:
    for p in sorted(input_dir.glob("*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            yield rec, p
        except Exception:
            continue


def escape(s: Optional[str]) -> str:
    return html.escape(s or "")


STYLES = """
      .container{max-width:960px;margin:0 auto;padding:16px}
      .header{display:flex;justify-content:space-between;align-items:center;gap:12px}
      .badges{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
      .btn{display:inline-block;padding:8px 10px;border:1px solid var(--border);border-radius:8px;color:#cfe7ff;text-decoration:none}
      .grid{display:grid;grid-template-columns:1.2fr .8fr;gap:16px;margin-top:16px}
      @media(max-width:840px){.grid{grid-template-columns:1fr}}
      .gal{width:100%;height:auto;border-radius:10px;margin-bottom:12px;background:#0f172a}
      .kv{display:flex;gap:10px;align-items:center;margin:6px 0;color:var(--muted)}
      .kv span{min-width:80px;color:#9fb3c8}
      .kv.warn b{color:#ffd08a}
"""


def render_page(rec: Dict[str, Any], site_origin: str) -> str:
    rid = rec.get("id") or ""
    title = _pick_title(rec) or "(제목 없음)"
    address = rec.get("address") or {}
    city = address.get("city") or ""
    street = address.get("street") or ""
    duration = rec.get("duration") or {}
    start = duration.get("start") or ""
    end = duration.get("end") or ""
    category = rec.get("category") or ""
    is_popup = bool(rec.get("isPopup"))
    geo = rec.get("geo") or {}
    lat = geo.get("lat")
    lon = geo.get("lon")
    images = rec.get("images") or []
    source_url = _pick_source_url(rec)
    thumb = _pick_thumb(rec)

    price_norm = ((rec.get("pricing") or {}).get("normalized") or {})
    detection = ((rec.get("meta") or {}).get("detection") or {})
    validation = ((rec.get("meta") or {}).get("validation") or {})

    desc = f"{title} — {city} {start}~{end}".strip()

    # JSON-LD Event schema (minimal)
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": title,
        "startDate": start or None,
        "endDate": end or None,
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {
            "@type": "Place",
            "name": city or None,
            "address": street or None,
            "geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon} if lat and lon else None,
        },
        "image": [img.get("url") for img in images if isinstance(img, dict) and img.get("url")],
        "url": source_url,
    }
    # prune Nones
    def prune(obj):
        if isinstance(obj, dict):
            return {k: prune(v) for k, v in obj.items() if v is not None}
        if isinstance(obj, list):
            return [prune(v) for v in obj if v is not None]
        return obj

    json_ld = prune(json_ld)

    og_image = thumb or (json_ld.get("image") or [None])[0]
    og_image_meta = f'<meta property="og:image" content="{escape(og_image)}" />' if og_image else ''

    # Build gallery HTML
    gallery = []
    for img in images:
        if not isinstance(img, dict) or not img.get("url"):
            continue
        u = img.get("url")
        gallery.append(f'<img class="gal" src="{escape(u)}" alt="image" loading="lazy" />')
    gallery_html = "\n        ".join(gallery)

    source_link_html = f'<a class="btn" href="{escape(source_url)}" target="_blank" rel="noopener">원문 보기</a>' if source_url else ''
    maps_link_html = (
        f'<a class="btn" href="https://maps.google.com/?q={lat},{lon}" target="_blank" rel="noopener">지도 열기</a>'
        if (lat is not None and lon is not None) else ''
    )

    price_html = ''
    if price_norm:
        cur = price_norm.get('currency') or ''
        a = price_norm.get('amountMin')
        b = price_norm.get('amountMax')
        if a is not None and b is not None:
            price_html = f'<div class="kv"><span>가격</span><b>{escape(cur)} {a:g} ~ {b:g}</b></div>'
        elif a is not None:
            price_html = f'<div class="kv"><span>가격</span><b>{escape(cur)} {a:g}</b></div>'

    detect_html = ''
    if detection:
        parts = [f"{escape(k)}: {escape(str(v))}" for k, v in detection.items()]
        detect_html = '<div class="kv"><span>판정 근거</span><b>' + ', '.join(parts) + '</b></div>'

    val_html = ''
    errs = (validation.get('errors') or []) if isinstance(validation, dict) else []
    warns = (validation.get('warnings') or []) if isinstance(validation, dict) else []
    if errs or warns:
        val_html = f'<div class="kv warn"><span>검증</span><b>오류 {len(errs)}, 경고 {len(warns)}</b></div>'

    popup_badge_html = '<span class="badge popup">POP-UP</span>' if is_popup else ''
    ads_meta = f'<meta name="google-adsense-account" content="{ADSENSE_PUB}" />'
    ads_script = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_PUB}" crossorigin="anonymous"></script>'

    return f"""<!doctype html>
<html lang=\"ko\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{escape(title)} | Pop-up Finder</title>
    <meta name=\"description\" content=\"{escape(desc)}\" />
    <link rel=\"canonical\" href=\"{site_origin}/p/{escape(rid)}.html\" />
    {ads_meta}
    {ads_script}
    <meta property=\"og:title\" content=\"{escape(title)}\" />
    <meta property=\"og:description\" content=\"{escape(desc)}\" />
    {og_image_meta}
    <script type=\"application/ld+json\">{json.dumps(json_ld, ensure_ascii=False)}</script>
    <link rel=\"stylesheet\" href=\"../styles.css?v=1\" />
    <style>
{STYLES}
    </style>
  </head>
  <body>
    <div class=\"container\"> 
      <div class=\"header\">
        <a class=\"btn\" href=\"../index.html\">← 목록</a>
        <h1 style=\"margin:8px 0;\">{escape(title)}</h1>
        <span style=\"flex:1\"></span>
        {source_link_html}
      </div>

      <div class=\"badges\">
        <span class=\"badge cat\">{escape(category or '—')}</span>
        {popup_badge_html}
        <span class=\"badge status\">{escape(start or '?')} ~ {escape(end or '?')}</span>
        {maps_link_html}
      </div>

      <div class=\"grid\">
        <div>
          {gallery_html}
        </div>
        <aside>
          <div class=\"kv\"><span>도시</span><b>{escape(city or '—')}</b></div>
          <div class=\"kv\"><span>주소</span><b>{escape(street or '—')}</b></div>
          <div class=\"kv\"><span>좌표</span><b>{escape(str(lat) if lat is not None else '—')}, {escape(str(lon) if lon is not None else '—')}</b></div>
          {price_html}
          {detect_html}
          {val_html}
        </aside>
      </div>
    </div>
    <footer class=\"site-footer\"><a href=\"../privacy.html\">Privacy Policy</a></footer>
  </body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Build static HTML detail pages and optional sitemap/robots")
    ap.add_argument("--input-dir", type=str, default=str(Path("data")/"popups"))
    ap.add_argument("--out-dir", type=str, default=str(Path("web")/"p"))
    ap.add_argument("--site-origin", type=str, default=SITE_ORIGIN, help="Site origin for canonical URLs and sitemap locs")
    ap.add_argument("--sitemap-out", type=str, default=None, help="Path to write sitemap.xml (optional)")
    ap.add_argument("--robots-out", type=str, default=None, help="Path to write robots.txt (optional)")
    args = ap.parse_args()

    src = Path(args.input_dir)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Collect for pages and optional sitemap
    total = 0
    url_items: list[tuple[str, str]] = []  # (loc, lastmod)

    def _pick_lastmod(rec: Dict[str, Any], src_path: Path) -> str:
        meta = (rec.get("meta") or {}) if isinstance(rec, dict) else {}
        # Prefer explicit timestamps if available
        for k in ("lastModified", "lastChanged", "updatedAt", "modifiedAt", "fetchedAt"):
            v = meta.get(k)
            if isinstance(v, str) and v.strip():
                # Normalize: if date only, add T00:00:00Z; if ISO-like, keep
                s = v.strip()
                if len(s) == 10 and s[4] == '-' and s[7] == '-':
                    return s + "T00:00:00Z"
                return s
        # Fallback to file mtime
        ts = dt.datetime.fromtimestamp(src_path.stat().st_mtime, tz=dt.timezone.utc)
        return ts.isoformat().replace('+00:00', 'Z')

    for rec, src_path in load_records(src):
        rid = rec.get("id")
        if not rid:
            continue
        html_text = render_page(rec, args.site_origin)
        (out / f"{rid}.html").write_text(html_text, encoding="utf-8")
        total += 1
        # Collect for sitemap
        loc = f"{args.site_origin}/p/{rid}.html"
        lastmod = _pick_lastmod(rec, src_path)
        url_items.append((loc, lastmod))

    print(f"Built pages: {total} -> {out}")

    # Optional sitemap.xml
    if args.sitemap_out:
        sm_path = Path(args.sitemap_out)
        sm_path.parent.mkdir(parents=True, exist_ok=True)
        # Add index and privacy
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
        static_urls = [
            (f"{args.site_origin}/", now_iso),
            (f"{args.site_origin}/privacy.html", now_iso),
        ]
        all_urls = static_urls + url_items
        parts = [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for loc, lm in all_urls:
            parts.append("  <url>")
            parts.append(f"    <loc>{html.escape(loc)}</loc>")
            parts.append(f"    <lastmod>{html.escape(lm)}</lastmod>")
            parts.append("  </url>")
        parts.append("</urlset>\n")
        sm_path.write_text("\n".join(parts), encoding="utf-8")
        print(f"Wrote sitemap: {sm_path}")

    # Optional robots.txt
    if args.robots_out:
        rb_path = Path(args.robots_out)
        rb_path.parent.mkdir(parents=True, exist_ok=True)
        rb = f"User-agent: *\nAllow: /\nSitemap: {args.site_origin}/sitemap.xml\n"
        rb_path.write_text(rb, encoding="utf-8")
        print(f"Wrote robots: {rb_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
