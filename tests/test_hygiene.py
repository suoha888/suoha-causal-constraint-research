from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_public_hygiene import digest, read_hashes, scan


class HygieneTests(unittest.TestCase):
    def test_hash_only_blocklist_detects_a_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "note.md").write_text("synthetic-blocked-marker\n", encoding="utf-8")
            blocked = root / "blocked.txt"
            blocked.write_text(digest("synthetic-blocked-marker") + "\n", encoding="utf-8")
            result = scan(root, read_hashes(blocked), root / "missing-policy.yaml")
            self.assertFalse(result["ok"])
            self.assertEqual(result["violations"][0]["type"], "blocked_digest")

    def test_clean_synthetic_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "note.md").write_text("clean synthetic note\n", encoding="utf-8")
            result = scan(root, set(), root / "missing-policy.yaml")
            self.assertTrue(result["ok"], result)


if __name__ == "__main__":
    unittest.main()
