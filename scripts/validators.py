from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import Draft7Validator, FormatChecker


_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "config" / "record.schema.json"


def _load_schema() -> Dict[str, Any]:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_FORMAT_CHECKER = FormatChecker()
_VALIDATOR = Draft7Validator(_load_schema(), format_checker=_FORMAT_CHECKER)


def _is_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except Exception:
        return False


def validate_record(rec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Return (errors, warnings) lists for a record.

    - Schema validation for required fields and basic types
    - Additional checks: coords range, duration order, link scheme
    """
    errors: List[str] = []
    warnings: List[str] = []

    # JSON schema
    for err in _VALIDATOR.iter_errors(rec):
        path = ".".join(str(p) for p in err.path)
        errors.append(f"schema:{path}:{err.message}")

    # Duration order
    dur = rec.get("duration") or {}
    s = dur.get("start") if isinstance(dur, dict) else None
    e = dur.get("end") if isinstance(dur, dict) else None
    if s and e and _is_date(s) and _is_date(e):
        try:
            sd = datetime.strptime(s, "%Y-%m-%d")
            ed = datetime.strptime(e, "%Y-%m-%d")
            if ed < sd:
                errors.append("duration:end_before_start")
        except Exception:
            warnings.append("duration:parse_failed")

    # Coordinates range
    geo = rec.get("geo") or {}
    lat = geo.get("lat") if isinstance(geo, dict) else None
    lon = geo.get("lon") if isinstance(geo, dict) else None
    if lat is not None:
        try:
            if not (-90.0 <= float(lat) <= 90.0):
                errors.append("geo:lat_out_of_range")
        except Exception:
            errors.append("geo:lat_invalid")
    if lon is not None:
        try:
            if not (-180.0 <= float(lon) <= 180.0):
                errors.append("geo:lon_out_of_range")
        except Exception:
            errors.append("geo:lon_invalid")

    # Link scheme
    for i, l in enumerate(rec.get("links") or []):
        if not isinstance(l, dict):
            continue
        href = l.get("href")
        if isinstance(href, str) and href:
            if not (href.startswith("http://") or href.startswith("https://")):
                warnings.append(f"links[{i}]:non_http_scheme")

    return errors, warnings

