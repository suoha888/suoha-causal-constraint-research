from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_research_case import validate_case


def fixture() -> dict:
    with (ROOT / "examples" / "synthetic-case.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


class ValidatorTests(unittest.TestCase):
    def test_synthetic_case_passes(self) -> None:
        result = validate_case(fixture())
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["derived_classification"], "RESEARCH_READY")

    def test_post_cutoff_supporting_evidence_is_rejected(self) -> None:
        case = fixture()
        case["evidence"][0]["known_at"] = "2026-09-16"
        result = validate_case(case)
        self.assertFalse(result["ok"])
        self.assertIn("temporal_leakage", {item["code"] for item in result["errors"]})

    def test_private_evidence_cannot_taint_public_case(self) -> None:
        case = fixture()
        case["evidence"][0]["access"] = "PRIVATE"
        result = validate_case(case)
        self.assertFalse(result["ok"])
        self.assertIn("private_evidence_taint", {item["code"] for item in result["errors"]})

    def test_internal_surface_can_inspect_private_metadata(self) -> None:
        case = fixture()
        case["evidence"][0]["access"] = "PRIVATE"
        result = validate_case(case, surface="internal")
        self.assertTrue(result["ok"], result)

    def test_advanced_supply_state_needs_evidence(self) -> None:
        case = fixture()
        case["constraints"][0]["state"] = "UNCOMMITTED_AVAILABLE"
        case["constraints"][0]["evidence_ids"] = []
        result = validate_case(case)
        self.assertFalse(result["ok"])
        self.assertIn("unsupported_supply_promotion", {item["code"] for item in result["errors"]})

    def test_downstream_gate_cannot_hide_failed_prerequisite(self) -> None:
        case = fixture()
        case["gates"]["G1_dependency_necessity"]["state"] = "FAIL"
        result = validate_case(case)
        self.assertFalse(result["ok"])
        self.assertIn("gate_compensation", {item["code"] for item in result["errors"]})

    def test_market_cap_must_reconcile(self) -> None:
        case = fixture()
        case["issuers"][0]["market"]["market_cap"] = 100
        result = validate_case(case)
        self.assertFalse(result["ok"])
        self.assertIn("market_cap_mismatch", {item["code"] for item in result["errors"]})

    def test_material_countercase_needs_disproof_plan(self) -> None:
        case = fixture()
        case["countercases"][0]["disproof_plan_ids"] = []
        result = validate_case(case)
        self.assertFalse(result["ok"])
        self.assertIn("missing_disproof", {item["code"] for item in result["errors"]})

    def test_unresolved_evidence_reference_is_rejected(self) -> None:
        case = fixture()
        case["edges"][0]["evidence_ids"] = ["ev-does-not-exist"]
        result = validate_case(case)
        self.assertFalse(result["ok"])
        self.assertIn("unknown_evidence_reference", {item["code"] for item in result["errors"]})

    def test_copy_of_fixture_is_not_mutated(self) -> None:
        original = fixture()
        candidate = copy.deepcopy(original)
        validate_case(candidate)
        self.assertEqual(candidate, original)


if __name__ == "__main__":
    unittest.main()
