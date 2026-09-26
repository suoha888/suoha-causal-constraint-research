import copy
import unittest
from test_v11_contract import fixture
from validate_research_case import validate_case
from gate_engine import derive_gates, derive_classification
from run_evals import evaluate_record
from pathlib import Path


class IntegrityTests(unittest.TestCase):
    def test_publicly_accessible_sources_are_accepted(self):
        case = fixture()
        for source in case["evidence"]:
            source["access_class"] = "PUBLICLY_ACCESSIBLE"
        result = validate_case(case)
        self.assertTrue(result["ok"], result)

    def test_bridge_evidence_must_be_usable(self):
        for state in ("STALE", "CONTRADICTED"):
            def change(case):
                source = copy.deepcopy(case["evidence"][0])
                source.update(evidence_id="bad-bridge-source", evidence_state=state)
                case["evidence"].append(source)
                for step in case["capital_bridges"][0]["steps"]:
                    step["evidence_ids"] = ["bad-bridge-source"]
            self.reject(change, "unsupported_bridge_evidence")

    def reject(self, change, code):
        case = fixture()
        change(case)
        result = validate_case(case)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["derived_classification"])
        self.assertIn(code, {e["code"] for e in result["errors"]}, result)

    def test_contradictions_do_not_support(self):
        self.reject(lambda c: [x.update(relation="CONTRADICT") for x in c["claim_evidence_links"]], "unsupported_claim")

    def test_link_ownership(self):
        self.reject(lambda c: c["claims"][0].update(evidence_links=["link-market"]), "link_ownership")

    def test_stale_evidence(self):
        self.reject(lambda c: [x.update(evidence_state="STALE") for x in c["evidence"]], "unsupported_evidence")

    def test_missing_dimension_source(self):
        self.reject(lambda c: c["constraints"][0]["dimension_assessments"][0].update(evidence_ids=["missing"]), "unknown_evidence_reference")

    def test_private_dimension_only(self):
        def change(c):
            source = copy.deepcopy(c["evidence"][0])
            source.update(evidence_id="private-only", access_class="PRIVATE")
            c["evidence"].append(source)
            c["constraints"][0]["dimension_assessments"][0]["evidence_ids"] = ["private-only"]
        self.reject(change, "private_evidence_taint")

    def test_gate_source(self):
        self.reject(lambda c: c["gates"]["G0_identity_time"].update(evidence_ids=["missing"]), "unknown_evidence_reference")

    def test_bridge_reference(self):
        self.reject(lambda c: c["issuers"][0].update(capital_bridge_steps=["missing"]), "unknown_reference")

    def test_disproof_reference(self):
        self.reject(lambda c: c["countercases"][0].update(disproof_plan_ids=["missing"]), "unknown_reference")

    def test_fake_formula(self):
        self.reject(lambda c: c["calculations"][0].update(formula="1 + 1 = 99999"), "calculation_integrity")

    def test_incorrect_operator(self):
        self.reject(lambda c: c["calculations"][0].update(formula="metric-price + metric-shares"), "calculation_integrity")

    def test_units(self):
        self.reject(lambda c: c["metrics"][1].update(unit="USD"), "calculation_integrity")

    def test_future_metric(self):
        self.reject(lambda c: c["metrics"][0].update(known_at="2099-01-01T00:00:00Z"), "temporal_leakage")

    def test_unknown_property(self):
        self.reject(lambda c: c.update(unrecognized="extra"), "schema_error")
        self.reject(lambda c: c.update(unrecognized={"evidence_ids":42}), "schema_error")
        self.reject(lambda c: c.update(transitions=[{"trigger_evidence_ids":42}]), "schema_error")

    def test_malformed_containers(self):
        for field in ("constraints", "issuers", "claims", "evidence", "gates", "transitions"):
            for value in (None, 42, "wrong"):
                with self.subTest(field=field, value=value):
                    self.reject(lambda c: c.update({field:value}), "schema_error")

    def test_eleven_unknown_dimensions(self):
        case = fixture()
        for dimension in case["constraints"][0]["dimension_assessments"]:
            if dimension["dimension"] not in {"system_necessity", "route_around_difficulty"}:
                dimension["status"] = "UNKNOWN"
        self.assertNotEqual(derive_gates(case)["G4_supply_constraint"]["state"], "PASS")

    def test_cancellation_never_positive(self):
        case = fixture()
        case["customer_signals"][0].update(signal_type="CANCELLATION", binding_status="CANCELLED")
        self.assertNotEqual(derive_gates(case)["G5_customer_validation"]["state"], "PASS")

    def test_negative_case_is_valid_research(self):
        case = fixture()
        case["constraints"][0]["status"] = "CONTRADICTED"
        case["edges"] = []
        case["gates"] = derive_gates(case)
        case["classification"] = derive_classification(case["gates"])
        result = validate_case(case)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["outcomes"]["constraint_thesis"], "REFUTED")
        self.assertEqual(result["derived_gates"]["G9_geo_policy"]["state"], "PASS")

    def test_eval_must_actually_execute(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertRaises(ValueError):
            evaluate_record(root, {"expected":"reject", "input_change":"some prose"})
        with self.assertRaises(ValueError):
            evaluate_record(root, {"expected":"reject", "fixture":"examples/synthetic-case-v1.1.json", "error_codes":["anything"]})

    def test_issuer_self_report_is_not_customer_validation(self):
        self.reject(lambda c: [s.update(source_perspective="ISSUER", independence_group="issuer-self-report") for s in c["evidence"] if s["evidence_id"] == "ev-customer"], "derived_gate_mismatch")

    def test_unqualified_edge_cannot_pass(self):
        self.reject(lambda c: c["edges"][0].update(qualification_status="NOT_QUALIFIED", customer_status="UNCONFIRMED"), "derived_gate_mismatch")

    def test_single_step_not_full_financial_transmission(self):
        def change(c):
            c["capital_bridges"][0]["steps"] = c["capital_bridges"][0]["steps"][:1]
            c["issuers"][0]["capital_bridge_steps"] = ["bridge-demand-volume"]
        self.reject(change, "derived_gate_mismatch")

    def test_market_anchor_matches_snapshot(self):
        self.reject(lambda c: c["expectation_gap"].update(market_anchor_value=1), "expectation_anchor_mismatch")

    def test_same_product_does_not_hide_wrong_inputs(self):
        self.reject(lambda c: c["issuers"][0]["market"].update(price=420, shares_outstanding=1000000), "market_ledger_mismatch")

    def test_unknown_bridge_does_not_require_invented_steps(self):
        case = fixture()
        case["capital_bridges"] = []
        case["issuers"][0]["capital_bridge_steps"] = []
        case["gates"] = derive_gates(case)
        case["classification"] = derive_classification(case["gates"])
        result = validate_case(case)
        self.assertTrue(result["ok"], result)
        self.assertNotEqual(result["derived_gates"]["G7_financial_transmission"]["state"], "PASS")
