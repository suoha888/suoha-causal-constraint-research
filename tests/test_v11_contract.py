from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_research_case import validate_case
from gate_engine import derive_gates, derive_classification


def fixture() -> dict:
    with (ROOT / "examples" / "synthetic-case-v1.1.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


class V11ContractTests(unittest.TestCase):
    def assert_code(self, case: dict, code: str, surface: str = "public") -> None:
        result = validate_case(case, surface=surface)
        self.assertFalse(result["ok"], result)
        self.assertIn(code, {item["code"] for item in result["errors"]}, result)

    def test_complete_v11_fixture_passes(self) -> None:
        result = validate_case(fixture())
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["derived_classification"], "RESEARCH_READY")
        self.assertEqual(result["summary"]["gates_passed"], 11)

    def test_all_thirteen_dimensions_are_required(self) -> None:
        case = fixture()
        case["constraints"][0]["dimension_assessments"].pop()
        self.assert_code(case, "incomplete_constraint_dimensions")

    def test_duplicate_dimension_is_rejected(self) -> None:
        case = fixture()
        case["constraints"][0]["dimension_assessments"][1]["dimension"] = "system_necessity"
        self.assert_code(case, "duplicate_dimension")

    def test_parallel_supply_states_are_not_a_promoted_ladder(self) -> None:
        case = fixture()
        case["constraints"][0]["supply_states"][3]["evidence_ids"] = []
        self.assert_code(case, "unsupported_supply_state")

    def test_edge_requires_product_and_scope(self) -> None:
        case = fixture()
        case["edges"][0]["product_or_process"] = ""
        self.assert_code(case, "missing_text")

    def test_supported_customer_signal_requires_evidence(self) -> None:
        case = fixture()
        case["customer_signals"][0]["evidence_ids"] = []
        self.assert_code(case, "unsupported_customer_signal")

    def test_claim_and_evidence_links_are_resolved(self) -> None:
        case = fixture()
        case["claim_evidence_links"][0]["evidence_id"] = "missing-evidence"
        self.assert_code(case, "unknown_reference")

    def test_unknown_claim_cannot_be_supported(self) -> None:
        case = fixture()
        case["claims"][0]["epistemic_type"] = "UNKNOWN"
        self.assert_code(case, "epistemic_conflict")

    def test_private_derived_claim_cannot_be_public(self) -> None:
        case = fixture()
        case["claims"][0]["derivation_access"] = "PRIVATE"
        case["claims"][0]["public_support_ids"] = []
        self.assert_code(case, "private_derivation_taint")

    def test_private_evidence_cannot_be_publicly_referenced(self) -> None:
        case = fixture()
        case["evidence"][0]["access_class"] = "PRIVATE"
        self.assert_code(case, "private_evidence_taint")

    def test_post_cutoff_source_is_rejected(self) -> None:
        case = fixture()
        case["evidence"][0]["known_at"] = "2026-09-19T00:00:00Z"
        self.assert_code(case, "temporal_leakage")

    def test_timezone_is_required_for_v11_times(self) -> None:
        case = fixture()
        case["evidence"][0]["known_at"] = "2026-09-18T00:00:00"
        self.assert_code(case, "timezone_required")

    def test_market_cap_must_reconcile(self) -> None:
        case = fixture()
        case["issuers"][0]["market"]["market_cap"] = 1
        self.assert_code(case, "market_cap_mismatch")

    def test_unknown_quote_can_be_explicit(self) -> None:
        case = fixture()
        market = case["issuers"][0]["market"]
        market.update({"quote_type": "UNKNOWN", "price": None, "price_as_of": None, "shares_outstanding": None, "shares_as_of": None, "market_cap": None, "market_cap_as_of": None, "enterprise_value": None, "status": "UNKNOWN", "source_ids": [], "calculation_ids": []})
        case["gates"] = derive_gates(case)
        case["classification"] = derive_classification(case["gates"])
        result = validate_case(case)
        self.assertTrue(result["ok"], result)
        self.assertNotEqual(result["derived_classification"], "RESEARCH_READY")

    def test_supported_market_state_needs_source(self) -> None:
        case = fixture()
        case["issuers"][0]["market"]["source_ids"] = []
        self.assert_code(case, "unsupported_market_state")

    def test_calculation_inputs_must_exist(self) -> None:
        case = fixture()
        case["calculations"][0]["input_metric_ids"] = ["missing-metric"]
        self.assert_code(case, "unknown_reference")

    def test_expectation_without_anchor_cannot_be_supported(self) -> None:
        case = fixture()
        case["expectation_gap"]["market_anchor_type"] = "UNKNOWN"
        self.assert_code(case, "unsupported_expectation")

    def test_gate_state_is_derived_not_trusted(self) -> None:
        case = fixture()
        case["gates"]["G4_supply_constraint"]["state"] = "UNKNOWN"
        self.assert_code(case, "derived_gate_mismatch")

    def test_classification_is_derived_not_trusted(self) -> None:
        case = fixture()
        case["classification"] = "MAP_ONLY"
        self.assert_code(case, "classification_mismatch")

    def test_material_countercase_needs_disproof_plan(self) -> None:
        case = fixture()
        case["countercases"][0]["disproof_plan_ids"] = []
        self.assert_code(case, "missing_disproof")

    def test_fatal_countercase_requires_invalidated_state(self) -> None:
        case = fixture()
        case["countercases"][0]["severity"] = "FATAL"
        case["countercases"][0]["status"] = "SUPPORTED"
        self.assert_code(case, "invalidated_state_mismatch")

    def test_fixture_is_not_mutated(self) -> None:
        original = fixture()
        candidate = copy.deepcopy(original)
        validate_case(candidate)
        self.assertEqual(candidate, original)


if __name__ == "__main__":
    unittest.main()
