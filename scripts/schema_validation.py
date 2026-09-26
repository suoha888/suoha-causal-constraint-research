"""Offline-only Draft 7 validation; never fetch a schema supplied by a case."""
import json
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7
from functools import lru_cache


@lru_cache(maxsize=8)
def validator(name="research-case-v1.1.schema.json"):
    root = Path(__file__).resolve().parents[1] / "schemas"
    documents = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in root.glob("*.json")}

    def normalize(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "$ref" and not item.startswith("#"):
                    filename, _, fragment = item.partition("#")
                    if filename not in documents:
                        raise ValueError(f"Unregistered local schema: {filename}")
                    value[key] = documents[filename]["$id"] + ("#" + fragment if fragment else "")
                else:
                    normalize(item)
        elif isinstance(value, list):
            for item in value:
                normalize(item)

    for document in documents.values():
        normalize(document)
        Draft7Validator.check_schema(document)
    registry = Registry().with_resources((d["$id"], Resource(contents=d, specification=DRAFT7)) for d in documents.values())
    return Draft7Validator(documents[name], registry=registry, format_checker=FormatChecker())


def schema_errors(case):
    return list(validator().iter_errors(case))
