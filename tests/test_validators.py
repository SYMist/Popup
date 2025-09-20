from __future__ import annotations

from scripts.validators import validate_record


def test_validator_ok():
    rec = {
        "id": "abc",
        "meta": {"fetchedAt": "2025-01-01T00:00:00Z"},
        "duration": {"start": "2025-01-01", "end": "2025-01-02"},
        "geo": {"lon": 127.0, "lat": 37.0},
        "links": [{"href": "https://example.com"}],
        "images": [{"url": "https://example.com/x.jpg", "role": "head"}],
    }
    errs, warns = validate_record(rec)
    assert not errs


def test_validator_detects_errors():
    rec = {
        "id": "abc",
        "meta": {"fetchedAt": "2025-01-01T00:00:00Z"},
        "duration": {"start": "2025-01-02", "end": "2025-01-01"},
        "geo": {"lon": 222.0, "lat": -200.0},
        "links": [{"href": "ftp://invalid.example"}],
        "images": [{"url": "not-a-url"}],
    }
    errs, warns = validate_record(rec)
    assert any("duration:end_before_start" in e for e in errs)
    assert any("geo:lat_out_of_range" in e or "geo:lon_out_of_range" in e for e in errs)
    assert any("non_http_scheme" in w for w in warns)
