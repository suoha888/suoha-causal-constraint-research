from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SchemaTests(unittest.TestCase):
    def test_all_schemas_are_parseable_and_project_scoped(self) -> None:
        paths = sorted((ROOT / "schemas").glob("*.json"))
        self.assertGreaterEqual(len(paths), 6)
        for path in paths:
            with path.open("r", encoding="utf-8") as handle:
                schema = json.load(handle)
            self.assertEqual(schema["type"], "object", path.name)
            self.assertIn("json-schema.org", schema["$schema"], path.name)
            self.assertTrue(schema["$id"].startswith("urn:suoha:"), path.name)

    def test_v11_schema_is_primary_strict_contract(self) -> None:
        path = ROOT / "schemas" / "research-case-v1.1.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.1")
        required = set(schema["required"])
        self.assertTrue({"data_availability", "claims", "metrics", "calculations", "reflexivity_audit"} <= required)

    def test_external_schema_references_resolve(self) -> None:
        for path in (ROOT / "schemas").glob("*.json"):
            schema = json.loads(path.read_text(encoding="utf-8"))
            refs = []

            def walk(value):
                if isinstance(value, dict):
                    if isinstance(value.get("$ref"), str) and not value["$ref"].startswith("#/"):
                        refs.append(value["$ref"].split("#", 1)[0])
                    for child in value.values():
                        walk(child)
                elif isinstance(value, list):
                    for child in value:
                        walk(child)

            walk(schema)
            for reference in refs:
                self.assertTrue((path.parent / reference).exists(), f"{path.name}: {reference}")


if __name__ == "__main__":
    unittest.main()
