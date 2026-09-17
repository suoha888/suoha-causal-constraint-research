#!/usr/bin/env python3
"""Validate the semantic contract of a causal research case.

The validator is intentionally dependency-free. It is a guardrail, not a
substitute for source review or investment judgment.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


GATE_KEYS = [
    "G0_identity_time",
    "G1_dependency_necessity",
    "G2_constraint_reality",
    "G3_edge_verification",
    "G4_capture_proof",
    "G5_financial_transmission",
    "G6_expectation_test",
    "G7_disproof_readiness",
]
GATE_STATES = {"PASS", "PARTIAL", "UNKNOWN", "STALE", "FAIL", "CONTRADICTED"}
EPISTEMIC = {"FACT", "INFERENCE", "HYPOTHESIS", "UNKNOWN", "CONTRADICTED"}
STATUSES = {"SUPPORTED", "PARTIAL", "STALE", "CONTRADICTED", "NOT_ESTABLISHED"}
ACCESS = {"PUBLIC", "RESTRICTED", "PRIVATE", "SYNTHETIC"}
SUPPLY_STATES = {
    "NAMEPLATE",
    "INSTALLED",
    "OPERABLE",
    "QUALIFIED",
    "MERCHANT",
    "CAPTIVE",
    "UNCOMMITTED_AVAILABLE",
}
SEVERITIES = {"LOCAL", "MATERIAL", "FATAL"}
CASE_STATES = {
    "DRAFT",
    "EVIDENCE_BUILDING",
    "TESTABLE",
    "SUPPORTED",
    "STRENGTHENED",
    "WEAKENED",
    "REVISED",
    "INVALIDATED",
    "CLOSED",
}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}")


def issue(errors: list[dict[str, str]], code: str, path: str, message: str) -> None:
    errors.append({"code": code, "path": path, "message": message})


def warning(warnings: list[dict[str, str]], code: str, path: str, message: str) -> None:
    warnings.append({"code": code, "path": path, "message": message})


def parse_date(
    value: Any,
    errors: list[dict[str, str]],
    path: str,
    required: bool = True,
) -> date | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        issue(errors, "invalid_date", path, "expected an ISO date or date-time")
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        return date.fromisoformat(value[:10])
    except ValueError:
        issue(errors, "invalid_date", path, "value is not a valid ISO date")
        return None


def require_dict(value: Any, errors: list[dict[str, str]], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        issue(errors, "wrong_type", path, "expected an object")
        return {}
    return value


def require_list(value: Any, errors: list[dict[str, str]], path: str) -> list[Any]:
    if not isinstance(value, list):
        issue(errors, "wrong_type", path, "expected an array")
        return []
    return value


def require_string(
    obj: dict[str, Any],
    key: str,
    errors: list[dict[str, str]],
    path: str,
    minimum: int = 1,
) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or len(value.strip()) < minimum:
        issue(errors, "missing_text", f"{path}.{key}", f"expected text with at least {minimum} characters")
        return ""
    return value


def require_enum(
    obj: dict[str, Any],
    key: str,
    choices: set[str],
    errors: list[dict[str, str]],
    path: str,
) -> str:
    value = require_string(obj, key, errors, path)
    if value and value not in choices:
        issue(errors, "invalid_enum", f"{path}.{key}", f"must be one of {sorted(choices)}")
    return value


def ids_from(obj: dict[str, Any], key: str, errors: list[dict[str, str]], path: str) -> list[str]:
    value = obj.get(key)
    if not isinstance(value, list):
        issue(errors, "wrong_type", f"{path}.{key}", "expected an array of IDs")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            issue(errors, "invalid_id", f"{path}.{key}[{index}]", "expected a non-empty string ID")
        else:
            result.append(item)
    return result


def unique_ids(
    records: list[Any],
    key: str,
    errors: list[dict[str, str]],
    path: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(records):
        item = require_dict(raw, errors, f"{path}[{index}]")
        value = item.get(key)
        if not isinstance(value, str) or not value.strip():
            issue(errors, "missing_id", f"{path}[{index}].{key}", "every record needs a stable ID")
            continue
        if value in result:
            issue(errors, "duplicate_id", f"{path}[{index}].{key}", f"duplicate ID: {value}")
        result[value] = item
    return result


def check_epistemic_status(
    obj: dict[str, Any],
    errors: list[dict[str, str]],
    path: str,
) -> None:
    require_enum(obj, "epistemic", EPISTEMIC, errors, path)
    require_enum(obj, "status", STATUSES, errors, path)


def referenced_ids(case: dict[str, Any]) -> set[str]:
    refs: set[str] = set()

    def add_from(obj: Any, key: str) -> None:
        if isinstance(obj, dict) and isinstance(obj.get(key), list):
            refs.update(item for item in obj[key] if isinstance(item, str))

    add_from(case.get("system_shift"), "evidence_ids")
    for key in ("constraints", "edges", "countercases", "disproof_plans", "transitions"):
        for item in case.get(key, []):
            add_from(item, "evidence_ids")
            add_from(item, "trigger_evidence_ids")
    for issuer in case.get("issuers", []):
        for key in ("exposure", "capture", "capital_bridge", "market"):
            add_from(issuer.get(key), "evidence_ids")
    if isinstance(case.get("expectation_gap"), dict):
        add_from(case["expectation_gap"], "evidence_ids")
    for gate in (case.get("gates") or {}).values():
        add_from(gate, "evidence_ids")
    return refs


def validate_case(case: Any, surface: str = "public") -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not isinstance(case, dict):
        issue(errors, "wrong_type", "$", "case must be a JSON object")
        return {"ok": False, "errors": errors, "warnings": warnings}

    required_top = [
        "schema_version",
        "case_id",
        "as_of",
        "research_cutoff",
        "question",
        "system_shift",
        "constraints",
        "edges",
        "issuers",
        "evidence",
        "gates",
        "countercases",
        "disproof_plans",
        "current_state",
        "transitions",
    ]
    for key in required_top:
        if key not in case:
            issue(errors, "missing_field", f"$.{key}", "required field is missing")

    if case.get("schema_version") != "1":
        issue(errors, "schema_version", "$.schema_version", "only schema version 1 is supported")
    case_id = require_string(case, "case_id", errors, "$", 3)
    as_of = parse_date(case.get("as_of"), errors, "$.as_of")
    cutoff = parse_date(case.get("research_cutoff"), errors, "$.research_cutoff")
    require_string(case, "question", errors, "$", 10)
    if as_of and cutoff and as_of < cutoff:
        issue(errors, "clock_order", "$", "as_of cannot precede research_cutoff")

    system_shift = require_dict(case.get("system_shift"), errors, "$.system_shift")
    if system_shift:
        require_string(system_shift, "claim_id", errors, "$.system_shift")
        require_string(system_shift, "description", errors, "$.system_shift", 10)
        check_epistemic_status(system_shift, errors, "$.system_shift")
        ids_from(system_shift, "evidence_ids", errors, "$.system_shift")
        parse_date(system_shift.get("event_date"), errors, "$.system_shift.event_date", required=False)

    evidence_records = require_list(case.get("evidence"), errors, "$.evidence")
    evidence = unique_ids(evidence_records, "id", errors, "$.evidence")
    for index, raw in enumerate(evidence_records):
        item = require_dict(raw, errors, f"$.evidence[{index}]")
        path = f"$.evidence[{index}]"
        require_string(item, "source_type", errors, path)
        require_string(item, "source_locator", errors, path, 3)
        known_at = parse_date(item.get("known_at"), errors, f"{path}.known_at")
        retrieved_at = parse_date(item.get("retrieved_at"), errors, f"{path}.retrieved_at")
        published_at = parse_date(item.get("published_at"), errors, f"{path}.published_at", required=False)
        access = require_enum(item, "access", ACCESS, errors, path)
        require_string(item, "independence_group", errors, path)
        check_epistemic_status(item, errors, path)
        supports = item.get("supports")
        if not isinstance(supports, bool):
            issue(errors, "wrong_type", f"{path}.supports", "expected a boolean")
            supports = False
        ids_from(item, "claim_ids", errors, path)
        if known_at and cutoff and known_at > cutoff and (supports or item.get("status") in {"SUPPORTED", "PARTIAL"}):
            issue(errors, "temporal_leakage", path, "post-cutoff evidence cannot support this replay")
        if published_at and cutoff and published_at > cutoff and supports:
            issue(errors, "publication_after_cutoff", path, "a post-cutoff publication cannot support this replay")
        if known_at and as_of and known_at > as_of and supports:
            issue(errors, "future_evidence", path, "evidence cannot be known after the case as-of date")
        if surface == "public" and access in {"PRIVATE", "RESTRICTED"}:
            warning(warnings, "non_public_record", path, "restricted metadata is retained but cannot support a public conclusion")
        if item.get("status") == "SUPPORTED" and item.get("epistemic") == "UNKNOWN":
            issue(errors, "epistemic_conflict", path, "UNKNOWN evidence cannot be marked SUPPORTED")
        if retrieved_at and known_at and retrieved_at < known_at:
            warning(warnings, "clock_warning", path, "retrieved_at precedes known_at; verify the source clocks")

    constraints_records = require_list(case.get("constraints"), errors, "$.constraints")
    constraints = unique_ids(constraints_records, "id", errors, "$.constraints")
    for index, raw in enumerate(constraints_records):
        item = require_dict(raw, errors, f"$.constraints[{index}]")
        path = f"$.constraints[{index}]"
        require_string(item, "label", errors, path, 3)
        dimensions = item.get("dimensions")
        if not isinstance(dimensions, list) or not dimensions:
            issue(errors, "missing_dimensions", f"{path}.dimensions", "at least one constraint dimension is required")
        state = require_enum(item, "state", SUPPLY_STATES, errors, path)
        check_epistemic_status(item, errors, path)
        evidence_ids = ids_from(item, "evidence_ids", errors, path)
        if state in {"QUALIFIED", "MERCHANT", "UNCOMMITTED_AVAILABLE"} and not evidence_ids:
            issue(errors, "unsupported_supply_promotion", path, "advanced supply states require direct evidence")
        if item.get("status") == "SUPPORTED" and not evidence_ids:
            issue(errors, "unsupported_constraint", path, "a supported constraint needs evidence")
        history = item.get("state_history")
        if history is not None:
            if not isinstance(history, list):
                issue(errors, "wrong_type", f"{path}.state_history", "expected an array")
            else:
                for h_index, history_item in enumerate(history):
                    h_path = f"{path}.state_history[{h_index}]"
                    h_obj = require_dict(history_item, errors, h_path)
                    require_enum(h_obj, "state", SUPPLY_STATES, errors, h_path)
                    parse_date(h_obj.get("observed_at"), errors, f"{h_path}.observed_at")
                    ids_from(h_obj, "evidence_ids", errors, h_path)

    edges_records = require_list(case.get("edges"), errors, "$.edges")
    edges = unique_ids(edges_records, "id", errors, "$.edges")
    for index, raw in enumerate(edges_records):
        item = require_dict(raw, errors, f"$.edges[{index}]")
        path = f"$.edges[{index}]"
        require_string(item, "from", errors, path)
        require_string(item, "to", errors, path)
        require_string(item, "relationship", errors, path)
        check_epistemic_status(item, errors, path)
        evidence_ids = ids_from(item, "evidence_ids", errors, path)
        parse_date(item.get("verified_at"), errors, f"{path}.verified_at", required=False)
        if item.get("status") == "SUPPORTED" and not evidence_ids:
            issue(errors, "unsupported_edge", path, "a supported dependency edge needs evidence")

    issuers_records = require_list(case.get("issuers"), errors, "$.issuers")
    issuers = unique_ids(issuers_records, "id", errors, "$.issuers")
    all_constraint_ids = set(constraints)
    for index, raw in enumerate(issuers_records):
        item = require_dict(raw, errors, f"$.issuers[{index}]")
        path = f"$.issuers[{index}]"
        require_string(item, "name", errors, path, 2)
        require_string(item, "role", errors, path)
        exposure = require_dict(item.get("exposure"), errors, f"{path}.exposure")
        capture = require_dict(item.get("capture"), errors, f"{path}.capture")
        bridge = require_dict(item.get("capital_bridge"), errors, f"{path}.capital_bridge")
        market = require_dict(item.get("market"), errors, f"{path}.market")

        if exposure:
            require_string(exposure, "path", errors, f"{path}.exposure", 5)
            exposure_constraints = ids_from(exposure, "constraint_ids", errors, f"{path}.exposure")
            unknown_constraints = sorted(set(exposure_constraints) - all_constraint_ids)
            if unknown_constraints:
                issue(errors, "unknown_reference", f"{path}.exposure.constraint_ids", f"unknown constraints: {unknown_constraints}")
            check_epistemic_status(exposure, errors, f"{path}.exposure")
            exposure_evidence = ids_from(exposure, "evidence_ids", errors, f"{path}.exposure")
            if exposure.get("status") == "SUPPORTED" and not exposure_evidence:
                issue(errors, "unsupported_exposure", f"{path}.exposure", "supported exposure needs evidence")
        if capture:
            require_string(capture, "mechanism", errors, f"{path}.capture", 5)
            score = capture.get("score")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 5:
                issue(errors, "invalid_score", f"{path}.capture.score", "capture score must be between 0 and 5")
            check_epistemic_status(capture, errors, f"{path}.capture")
            capture_evidence = ids_from(capture, "evidence_ids", errors, f"{path}.capture")
            if capture.get("status") == "SUPPORTED" and not capture_evidence:
                issue(errors, "unsupported_capture", f"{path}.capture", "supported capture needs evidence")
            if isinstance(score, (int, float)) and score >= 3 and not capture_evidence:
                issue(errors, "high_capture_without_evidence", f"{path}.capture", "a material capture score needs evidence")
            if exposure.get("status") == "NOT_ESTABLISHED" and isinstance(score, (int, float)) and score >= 2:
                issue(errors, "capture_without_exposure", f"{path}.capture", "capture cannot be promoted before exposure is established")
        if bridge:
            bridge_fields = [
                "driver_to_volume",
                "volume_to_revenue",
                "revenue_to_gross_profit",
                "gross_profit_to_cash",
                "cash_to_capital",
                "capital_to_per_share",
            ]
            for field in bridge_fields:
                require_string(bridge, field, errors, f"{path}.capital_bridge", 3)
            check_epistemic_status(bridge, errors, f"{path}.capital_bridge")
            bridge_evidence = ids_from(bridge, "evidence_ids", errors, f"{path}.capital_bridge")
            if bridge.get("status") == "SUPPORTED" and not bridge_evidence:
                issue(errors, "unsupported_bridge", f"{path}.capital_bridge", "supported capital transmission needs evidence")
        if market:
            require_string(market, "currency", errors, f"{path}.market", 3)
            numeric_values: dict[str, float] = {}
            for field in ("price", "shares_outstanding", "market_cap"):
                value = market.get(field)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                    issue(errors, "invalid_market_number", f"{path}.market.{field}", "expected a finite non-negative number")
                else:
                    numeric_values[field] = float(value)
            price_date = parse_date(market.get("price_as_of"), errors, f"{path}.market.price_as_of")
            require_string(market, "market_cap_method", errors, f"{path}.market")
            check_epistemic_status(market, errors, f"{path}.market")
            market_evidence = ids_from(market, "evidence_ids", errors, f"{path}.market")
            if market.get("status") == "SUPPORTED" and not market_evidence:
                issue(errors, "unsupported_market_state", f"{path}.market", "market state needs evidence")
            if {"price", "shares_outstanding", "market_cap"} <= numeric_values.keys():
                expected = numeric_values["price"] * numeric_values["shares_outstanding"]
                observed = numeric_values["market_cap"]
                tolerance = market.get("tolerance", 0.02)
                if not isinstance(tolerance, (int, float)) or tolerance < 0 or tolerance > 0.25:
                    issue(errors, "invalid_tolerance", f"{path}.market.tolerance", "tolerance must be between 0 and 0.25")
                    tolerance = 0.02
                if expected == 0:
                    if observed != 0:
                        issue(errors, "market_cap_mismatch", f"{path}.market", "zero inputs cannot produce a non-zero market cap")
                elif abs(observed - expected) / expected > tolerance:
                    issue(errors, "market_cap_mismatch", f"{path}.market", "market cap does not reconcile to price times shares")
            if price_date and cutoff and price_date > cutoff and market.get("epistemic") == "FACT":
                warning(warnings, "market_after_cutoff", f"{path}.market", "market observation is newer than the replay cutoff")

    expectation_gap = case.get("expectation_gap")
    if expectation_gap is not None:
        expectation_gap = require_dict(expectation_gap, errors, "$.expectation_gap")
        require_string(expectation_gap, "claim", errors, "$.expectation_gap", 5)
        require_string(expectation_gap, "market_implied", errors, "$.expectation_gap", 3)
        require_string(expectation_gap, "research_implied", errors, "$.expectation_gap", 3)
        check_epistemic_status(expectation_gap, errors, "$.expectation_gap")
        ids_from(expectation_gap, "evidence_ids", errors, "$.expectation_gap")

    gates_obj = require_dict(case.get("gates"), errors, "$.gates")
    gate_states: list[str] = []
    if gates_obj:
        for key in GATE_KEYS:
            if key not in gates_obj:
                issue(errors, "missing_gate", f"$.gates.{key}", "all ordered gates are required")
                continue
            gate = require_dict(gates_obj[key], errors, f"$.gates.{key}")
            state = require_enum(gate, "state", GATE_STATES, errors, f"$.gates.{key}")
            require_string(gate, "reason", errors, f"$.gates.{key}", 3)
            ids_from(gate, "evidence_ids", errors, f"$.gates.{key}")
            gate_states.append(state)
        for index, state in enumerate(gate_states):
            if state != "PASS":
                for later_index in range(index + 1, len(gate_states)):
                    if gate_states[later_index] == "PASS":
                        issue(
                            errors,
                            "gate_compensation",
                            f"$.gates.{GATE_KEYS[later_index]}",
                            f"cannot PASS while prerequisite {GATE_KEYS[index]} is {state}",
                        )

    countercases_records = require_list(case.get("countercases"), errors, "$.countercases")
    countercases = unique_ids(countercases_records, "id", errors, "$.countercases")
    for index, raw in enumerate(countercases_records):
        item = require_dict(raw, errors, f"$.countercases[{index}]")
        path = f"$.countercases[{index}]"
        severity = require_enum(item, "severity", SEVERITIES, errors, path)
        require_string(item, "claim", errors, path, 5)
        check_epistemic_status(item, errors, path)
        ids_from(item, "evidence_ids", errors, path)
        plan_ids = ids_from(item, "disproof_plan_ids", errors, path)
        if severity in {"MATERIAL", "FATAL"} and not plan_ids:
            issue(errors, "missing_disproof", path, "material and fatal countercases need a disproof plan")

    plans_records = require_list(case.get("disproof_plans"), errors, "$.disproof_plans")
    plans = unique_ids(plans_records, "id", errors, "$.disproof_plans")
    claim_ids = set(constraints) | set(edges) | set(issuers)
    if isinstance(system_shift.get("claim_id"), str):
        claim_ids.add(system_shift["claim_id"])
    for index, raw in enumerate(plans_records):
        item = require_dict(raw, errors, f"$.disproof_plans[{index}]")
        path = f"$.disproof_plans[{index}]"
        target = require_string(item, "target_claim_id", errors, path)
        if target and target not in claim_ids:
            issue(errors, "unknown_reference", f"{path}.target_claim_id", f"unknown claim ID: {target}")
        for field in ("test", "signal", "threshold", "window", "action", "owner"):
            require_string(item, field, errors, path, 1 if field in {"threshold", "window", "owner"} else 3)
        check_epistemic_status(item, errors, path)
        ids_from(item, "evidence_ids", errors, path)

    transition_records = require_list(case.get("transitions"), errors, "$.transitions")
    transitions = unique_ids(transition_records, "id", errors, "$.transitions")
    for index, raw in enumerate(transition_records):
        item = require_dict(raw, errors, f"$.transitions[{index}]")
        path = f"$.transitions[{index}]"
        from_state = require_enum(item, "from", CASE_STATES, errors, path)
        to_state = require_enum(item, "to", CASE_STATES, errors, path)
        parse_date(item.get("occurred_at"), errors, f"{path}.occurred_at")
        require_string(item, "reason", errors, path, 3)
        ids_from(item, "trigger_evidence_ids", errors, path)
        require_string(item, "case_version", errors, path)
        if from_state == to_state:
            issue(errors, "no_op_transition", path, "a transition must change state")
    current_state = require_enum(case, "current_state", CASE_STATES, errors, "$")
    if current_state != "DRAFT" and not transitions:
        issue(errors, "missing_transition_log", "$.transitions", "non-draft cases need an append-only transition log")

    all_refs = referenced_ids(case)
    unknown_refs = sorted(all_refs - set(evidence))
    if unknown_refs:
        issue(errors, "unknown_evidence_reference", "$", f"unresolved evidence IDs: {unknown_refs}")
    if surface == "public":
        private_refs = sorted(ref for ref in all_refs if ref in evidence and evidence[ref].get("access") in {"PRIVATE", "RESTRICTED"})
        if private_refs:
            issue(errors, "private_evidence_taint", "$", f"public case references restricted/private evidence: {private_refs}")

    fatal_supported = any(
        item.get("severity") == "FATAL" and item.get("status") == "SUPPORTED"
        for item in countercases.values()
    )
    if fatal_supported and current_state != "INVALIDATED":
        issue(errors, "invalidated_state_mismatch", "$.current_state", "a supported fatal countercase requires INVALIDATED")
    if current_state == "INVALIDATED" and not fatal_supported:
        warning(warnings, "invalidated_without_fatal", "$.current_state", "state is INVALIDATED but no supported fatal countercase is recorded")

    if gate_states and all(state == "PASS" for state in gate_states):
        derived_classification = "RESEARCH_READY"
    elif len(gate_states) >= 6 and all(state == "PASS" for state in gate_states[:6]):
        derived_classification = "OPERATING_CASE"
    elif len(gate_states) >= 3 and all(state == "PASS" for state in gate_states[:3]):
        derived_classification = "CONSTRAINT_CASE"
    else:
        derived_classification = "MAP_ONLY"
    if fatal_supported:
        derived_classification = "INVALIDATED"

    return {
        "ok": not errors,
        "case_id": case_id,
        "derived_classification": derived_classification,
        "surface": surface,
        "summary": {
            "evidence": len(evidence),
            "constraints": len(constraints),
            "edges": len(edges),
            "issuers": len(issuers),
            "countercases": len(countercases),
            "disproof_plans": len(plans),
            "gates_passed": sum(state == "PASS" for state in gate_states),
        },
        "errors": errors,
        "warnings": warnings,
    }


def load_case(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a causal research case")
    parser.add_argument("case", help="JSON case path, or - for stdin")
    parser.add_argument(
        "--surface",
        choices=("public", "internal"),
        default="public",
        help="public rejects restricted/private evidence references",
    )
    args = parser.parse_args()
    try:
        case = load_case(args.case)
    except (OSError, json.JSONDecodeError) as exc:
        result = {
            "ok": False,
            "errors": [{"code": "input_error", "path": args.case, "message": str(exc)}],
            "warnings": [],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    result = validate_case(case, args.surface)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
