#!/usr/bin/env python3
"""Check that every checked-in schema is valid JSON with basic metadata."""

from __future__ import annotations

import json
import re
import sys
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    schema_root = root / "schemas"
    errors: list[str] = []
    count = 0
    for path in sorted(schema_root.glob("*.json")):
        count += 1
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.name}: root must be an object")
            continue
        try:
            Draft7Validator.check_schema(value)
        except SchemaError as exc:
            errors.append(f"{path.name}: {exc.message}")
        if not isinstance(value.get("$schema"), str) or "json-schema.org" not in value["$schema"]:
            errors.append(f"{path.name}: missing JSON Schema dialect")
        if not isinstance(value.get("$id"), str) or not value["$id"].startswith("urn:suoha:"):
            errors.append(f"{path.name}: missing project-owned schema ID")
        if value.get("type") != "object":
            errors.append(f"{path.name}: root type must be object")
        required = value.get("required")
        if not isinstance(required, list) or len(required) != len(set(required)):
            errors.append(f"{path.name}: required must be a list with unique field names")
        for reference in re.findall(r'\"\$ref\"\s*:\s*\"([^\"]+)\"', json.dumps(value)):
            if reference.startswith("#/"):
                continue
            target = (path.parent / reference.split("#", 1)[0]).resolve()
            if not target.exists():
                errors.append(f"{path.name}: missing external schema reference {reference}")
    result = {"ok": not errors, "schemas_checked": count, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
