from __future__ import annotations

import json

from scripts.triple_client import parse_next_data, get_apollo_state, extract_festa


def _wrap_next_data(obj: dict) -> str:
    return f'<html><head></head><body><script id="__NEXT_DATA__">{json.dumps(obj)}</script></body></html>'


def test_parse_legacy_apollo_state():
    festa = {
        "__typename": "Festa",
        "resourceId": "00000000-0000-0000-0000-000000000000",
        "title": "Brand POP-UP",
        "category": "POP-UP",
        "duration": {"start": "2025-01-01", "end": "2025-01-31"},
        "address": {"city": "Seoul", "street": "Road"},
        "geolocation": {"coordinates": [127.0, 37.0]},
        "links": [{"href": "https://example.com", "label": "More"}],
        "images": [{"url": "https://example.com/a.jpg", "role": "content"}],
    }
    next_data = {"props": {"pageProps": {"apolloState": {"ROOT_QUERY": {"getFesta": festa}}}}}
    html = _wrap_next_data(next_data)
    nd = parse_next_data(html)
    assert nd is not None
    ap = get_apollo_state(nd)
    assert ap is not None
    res = extract_festa(ap)
    assert res is not None
    assert res["resourceId"] == festa["resourceId"]
    assert res["category"] == "POP-UP"
    assert res["images"][0]["url"].startswith("https://")


def test_parse_apollo_cache():
    festa = {
        "__typename": "Festa",
        "resourceId": "11111111-1111-1111-1111-111111111111",
        "title": "Some Festa",
        "category": "ENTER",
        "duration": {"start": "2025-02-01", "end": "2025-02-10"}
    }
    apollo_cache = {"ROOT_QUERY": {"getFesta": festa}}
    next_data = {"props": {"pageProps": {"__APOLLO_CACHE__": apollo_cache}}}
    html = _wrap_next_data(next_data)
    nd = parse_next_data(html)
    assert nd is not None
    ap = get_apollo_state(nd)
    assert ap is not None
    res = extract_festa(ap)
    assert res is not None
    assert res["resourceId"] == festa["resourceId"]
