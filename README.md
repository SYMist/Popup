# Popup Crawler

Weekly crawler that discovers Festa pages on the target service and extracts popup-store events from SSR Apollo State, saving normalized JSON and a SQLite snapshot.

## What it does
- Discovers Festa detail URLs via `sitemap-index.xml` → `sitemap-festa-detail-urls-*.xml`.
- Fetches detail pages for `ko`, `en`, `ja` locales: `/{lang}/content/festas/{id}`.
- Parses Next.js `__NEXT_DATA__` JSON → `apolloState` → `Festa` entity.
- Classifies popups by category allowlist and keyword/duration heuristics.
- Saves JSON to `data/popups/{id}.json` and updates `data/popups.sqlite`.

## Image rules
- Representative: `headImage` if present; otherwise first content image.
- Gallery: up to 5 more images, excluding representative, de-duplicated by URL.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/crawl_popups.py  # optional: limit with an integer arg
```

## GitHub Actions
- Workflow: `.github/workflows/crawl-popups.yml`
- Schedule: weekly at 19:00 UTC (Mon 04:00 KST)
- Artifacts: entire `data/` folder (JSON + SQLite)
- PR: JSON changes only (under `data/popups/`)

## TODO
- 상세한 진행 항목은 `docs/TODO.md`를 확인하세요.

## JSON schema (simplified)
```jsonc
{
  "id": "<resourceId>",
  "category": "POPUP",
  "duration": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "geo": { "lon": 126.0, "lat": 37.0 },
  "address": { "city": "Seoul", "street": "..." },
  "images": [{ "url": "...", "variant": "large", "role": "head" }],
  "links": [{ "href": "...", "label": "..." }],
  "pricing": { "type": "...", "description": "..." },
  "translations": { "ko": { "title": "...", "address": "..." }, "en": {}, "ja": {} },
  "source": { "koUrl": "...", "enUrl": "...", "jaUrl": "..." },
  "isPopup": true,
  "meta": { "fetchedAt": "2025-01-01T00:00:00Z", "detection": {"rule": "category|keyword|duration"} }
}
```

## Notes
- Respects robots.txt (Allow: /) and uses gentle rate limiting.
- No GraphQL direct calls; relies on SSR data to avoid introspection/auth constraints.
