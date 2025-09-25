# Popup Crawler

Weekly crawler that discovers Festa pages on the target service and extracts popup-store events from SSR Apollo State, saving normalized JSON and a SQLite snapshot.

## What it does
- Discovers Festa detail URLs via `https://triple.global/sitemap-index.xml` → `sitemap-festa-detail-urls-*.xml`.
- Fetches Festa detail pages from Interpark Global for preferred locales `zh-cn`, `en`, `ja`, `ko`: `https://interparkglobal.com/{lang}/festas/{id}`.
- Parses Next.js `__NEXT_DATA__` JSON and supports both legacy `apolloState` and `pageProps.__APOLLO_CACHE__` to extract the `Festa` entity.
- Classifies popups with a normalized category allowlist (e.g., `POP-UP`/`POP UP`/`POPUP_EVENT` → popup). Keyword/duration heuristics are planned.
- Saves JSON to `data/popups/{id}.json` and updates `data/popups.sqlite`. Records are tagged with `isPopup` and `meta.detection` but not filtered out at save time.

## Image rules
- Representative: `headImage` if present; otherwise first content image.
- Gallery: up to 5 more images, excluding representative, de-duplicated by URL.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Basic run
python scripts/crawl_popups.py

# Useful options
#   --limit N       Limit number of Festa IDs
#   --fast          Stop after first successful locale
#   --workers N     Concurrency (default: 8)
#   --qps Q         Global requests/sec (default: 2.0)
#   --langs list    Comma-separated locale order (default: zh-cn,en,ja,ko)
python scripts/crawl_popups.py --limit 50 --fast --workers 8 --qps 2.0
```

## Live Site
- Viewer: https://symist.github.io/Popup/

## GitHub Actions
- Workflow: `.github/workflows/crawl-popups.yml`
- Schedule: weekly at 19:00 UTC (Mon 04:00 KST)
- Data artifacts: entire `data/` folder (JSON + SQLite)
- Commit policy: changes under `data/**/*.json` are committed directly to `main` with a summary of added/modified/deleted counts.
- Pages deploy: builds web index (`web/data/index.json`) and static detail pages (`web/p/*.html`), uploads as Pages artifact, then deploys via `deploy-pages`.

## Build the web viewer locally
```bash
# Generate index (single file; auto-shards to monthly if >5MB)
python scripts/build_index.py --output data/index.json

# Generate static detail pages
python scripts/build_pages.py --out-dir web/p

# Preview
python -m http.server 8000
# Then open http://localhost:8000/web/
```

If you serve only the `web/` directory, also generate index under `web/data`:
```bash
python scripts/build_index.py --output web/data/index.json
python -m http.server -d web 8000
```

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
  "meta": {
    "fetchedAt": "2025-01-01T00:00:00Z",
    "detection": {
      "rule": "category",
      "category": "POP-UP"
    }
  }
}
```

## Notes
- Respects robots.txt (Allow: /) and uses gentle rate limiting.
- No GraphQL direct calls; relies on SSR data to avoid introspection/auth constraints.
- Current classification writes tags only; filtering to popups can be enabled later if needed by downstreams.
- Storage reduces churn: ignores `meta.fetchedAt` when comparing on-disk vs new record, so unchanged content doesn't cause needless JSON modifications.
