from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import Draft202012Validator


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_array(schema_path: Path, data: Any, context: str) -> List[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors: List[str] = []
    for err in validator.iter_errors(data):
        loc = "/".join([str(p) for p in err.absolute_path])
        errors.append(f"[{context}] {loc}: {err.message}")
    return errors


def validate_monthly(base_dir: Path, schema_path: Path, manifest: Dict[str, Any]) -> Tuple[int, List[str]]:
    months = manifest.get("months") or []
    total = 0
    all_errors: List[str] = []
    for m in months:
        name = "index-unknown.json" if m == "unknown" else f"index-{m}.json"
        p = base_dir / name
        if not p.exists():
            all_errors.append(f"[manifest] missing shard file: {p}")
            continue
        arr = load_json(p)
        if not isinstance(arr, list):
            all_errors.append(f"[{name}] not an array")
            continue
        total += len(arr)
        all_errors.extend(validate_array(schema_path, arr, name))
    return total, all_errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate built index.json or monthly shards against schema")
    ap.add_argument("--base", type=str, default=str(Path("web") / "data"), help="Directory containing index.json and shards")
    ap.add_argument("--schema", type=str, default=str(Path("config") / "index.schema.json"))
    args = ap.parse_args()

    base = Path(args.base)
    schema_path = Path(args.schema)
    manifest_path = base / "index-manifest.json"
    index_path = base / "index.json"

    if manifest_path.exists():
        manifest = load_json(manifest_path)
        mode = manifest.get("mode")
        if mode == "monthly":
            total, errors = validate_monthly(base, schema_path, manifest)
            print(f"Validated monthly shards: total_items={total}, files={len(manifest.get('months') or [])}")
            if errors:
                print("Validation errors:")
                for e in errors:
                    print(" -", e)
                return 1
            return 0
        else:
            # single
            if not index_path.exists():
                print("index.json not found while manifest mode=single")
                return 1
            arr = load_json(index_path)
            if not isinstance(arr, list):
                print("index.json is not an array")
                return 1
            errors = validate_array(schema_path, arr, "index.json")
            if errors:
                print("Validation errors:")
                for e in errors:
                    print(" -", e)
                return 1
            print(f"Validated single index: items={len(arr)}")
            return 0
    else:
        if not index_path.exists():
            print("Neither index-manifest.json nor index.json present in base directory")
            return 1
        arr = load_json(index_path)
        if not isinstance(arr, list):
            print("index.json is not an array")
            return 1
        errors = validate_array(schema_path, arr, "index.json")
        if errors:
            print("Validation errors:")
            for e in errors:
                print(" -", e)
            return 1
        print(f"Validated single index (no manifest): items={len(arr)}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

