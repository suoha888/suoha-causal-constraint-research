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


if __name__ == "__main__":
    unittest.main()
