#!/usr/bin/env python3
"""Validate the semantic contract of a causal research case.

The validator uses offline JSON Schema and semantic checks. It is a guardrail, not a
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_engine import GATE_KEYS as V11_GATE_KEYS
from gate_engine import derive_classification, derive_gates
from schema_validation import schema_errors
from semantic_integrity import integrity_errors, research_outcomes


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

    if case.get("schema_version") == "1.1":
        return validate_case_v11(case, surface)

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


V11_DIMENSIONS = {
    "system_necessity",
    "route_around_difficulty",
    "qualified_supplier_depth",
    "qualification_friction",
    "supply_ramp_latency",
    "yield_stability",
    "capacity_observability",
    "merchant_supply_availability",
    "geographic_policy_concentration",
    "customer_commitment",
    "price_realization",
    "capture_retention",
    "capital_efficiency",
}
V11_EVIDENCE_STATES = {"SUPPORTED", "PARTIAL", "STALE", "CONTRADICTED", "NOT_ESTABLISHED", "UNKNOWN"}
V11_ACCESS = {"PUBLICLY_ACCESSIBLE", "RESTRICTED_ACCESS", "PRIVATE", "SYNTHETIC"}
V11_EPISTEMIC = {"FACT", "INFERENCE", "HYPOTHESIS", "UNKNOWN"}
V11_CLASSIFICATIONS = {
    "MAP_ONLY",
    "CONSTRAINT_CASE",
    "CUSTOMER_VALIDATED_CASE",
    "OPERATING_CASE",
    "VARIANT_CASE",
    "RESEARCH_READY",
    "INVALIDATED",
}


def parse_v11_time(
    value: Any,
    errors: list[dict[str, str]],
    path: str,
    required: bool = True,
) -> datetime | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        issue(errors, "invalid_datetime", path, "expected an ISO-8601 date-time")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        issue(errors, "invalid_datetime", path, "expected a valid ISO-8601 date-time")
        return None
    if parsed.tzinfo is None:
        issue(errors, "timezone_required", path, "v1.1 time fields require an explicit timezone")
        return None
    return parsed


def v11_number(
    obj: dict[str, Any],
    key: str,
    errors: list[dict[str, str]],
    path: str,
    required: bool = True,
    allow_null: bool = False,
) -> float | None:
    value = obj.get(key)
    if value is None and (allow_null or not required):
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        issue(errors, "invalid_number", f"{path}.{key}", "expected a finite number")
        return None
    return float(value)


def v11_ids(
    obj: dict[str, Any],
    key: str,
    errors: list[dict[str, str]],
    path: str,
    required: bool = True,
) -> list[str]:
    value = obj.get(key)
    if value is None and not required:
        return []
    return ids_from(obj, key, errors, path)


def _v11_status(value: Any) -> str:
    return value if isinstance(value, str) else "UNKNOWN"


def _v11_public_refs(ids: set[str], evidence: dict[str, dict[str, Any]], surface: str, errors: list[dict[str, str]]) -> None:
    if surface != "public":
        return
    restricted = sorted(
        evidence_id
        for evidence_id in ids
        if evidence_id in evidence and evidence[evidence_id].get("access_class") in {"RESTRICTED_ACCESS", "PRIVATE"}
    )
    if restricted:
        issue(errors, "private_evidence_taint", "$", f"public case references restricted/private evidence: {restricted}")


def validate_case_v11(case: dict[str, Any], surface: str = "public") -> dict[str, Any]:
    """Validate schema first, then evidence and economic invariants."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    shape_errors = schema_errors(case)
    for error in shape_errors:
        issue(errors, "schema_error", error.json_path, error.message)
    # Do not run semantic traversals over malformed containers or absent fields.
    if any(error.validator in {"type", "required", "additionalProperties"} for error in shape_errors):
        return {"ok": False, "derived_classification": None, "derived_gates": {}, "errors": errors, "warnings": warnings}
    errors.extend(integrity_errors(case, surface))
    required_top = [
        "schema_version", "case_id", "as_of", "research_cutoff", "question",
        "security_identity", "data_availability", "system_shift", "claims",
        "claim_evidence_links", "evidence", "metrics", "calculations", "constraints",
        "edges", "customer_signals", "issuers", "expectation_gap", "reflexivity_audit",
        "gates", "countercases", "disproof_plans", "classification", "current_state", "transitions",
    ]
    for key in required_top:
        if key not in case:
            issue(errors, "missing_field", f"$.{key}", "required v1.1 field is missing")
    if case.get("schema_version") != "1.1":
        issue(errors, "schema_version", "$.schema_version", "only schema version 1.1 is supported by the strict validator")

    case_id = require_string(case, "case_id", errors, "$", 3)
    as_of = parse_v11_time(case.get("as_of"), errors, "$.as_of")
    cutoff = parse_v11_time(case.get("research_cutoff"), errors, "$.research_cutoff")
    require_string(case, "question", errors, "$", 10)
    if as_of and cutoff and as_of < cutoff:
        issue(errors, "clock_order", "$", "as_of cannot precede research_cutoff")

    identity = require_dict(case.get("security_identity"), errors, "$.security_identity")
    for field in ("issuer_id", "legal_name", "ticker", "exchange", "security_type", "primary_listing", "trading_currency"):
        require_string(identity, field, errors, "$.security_identity", 1)
    identity_status = require_enum(identity, "status", {"SUPPORTED", "PARTIAL", "UNKNOWN"}, errors, "$.security_identity")
    identity_evidence = set(v11_ids(identity, "evidence_ids", errors, "$.security_identity", required=False))

    availability = require_dict(case.get("data_availability"), errors, "$.data_availability")
    require_string(availability, "manifest_id", errors, "$.data_availability", 3)
    parse_v11_time(availability.get("as_of"), errors, "$.data_availability.as_of")
    adapters = require_list(availability.get("adapters"), errors, "$.data_availability.adapters")
    for index, raw in enumerate(adapters):
        item = require_dict(raw, errors, f"$.data_availability.adapters[{index}]")
        path = f"$.data_availability.adapters[{index}]"
        for field in ("adapter_id", "provider", "latency_class", "entitlement_status"):
            require_string(item, field, errors, path, 1)
        v11_ids(item, "capabilities", errors, path)
        v11_ids(item, "markets", errors, path)
        require_enum(item, "availability", {"AVAILABLE", "DEGRADED", "AUTH_REQUIRED", "UNAVAILABLE", "NOT_SUPPORTED"}, errors, path)
        parse_v11_time(item.get("last_success_at"), errors, f"{path}.last_success_at", required=False)

    evidence_records = require_list(case.get("evidence"), errors, "$.evidence")
    evidence = unique_ids(evidence_records, "evidence_id", errors, "$.evidence")
    for index, raw in enumerate(evidence_records):
        item = require_dict(raw, errors, f"$.evidence[{index}]")
        path = f"$.evidence[{index}]"
        for field in ("source_type", "source_locator", "source_perspective", "access_class", "redistribution_rights", "citation_status", "independence_group", "evidence_state"):
            if field in {"access_class", "redistribution_rights", "citation_status", "evidence_state"}:
                continue
            require_string(item, field, errors, path, 1)
        require_enum(item, "source_perspective", {"REGULATOR", "EXCHANGE", "ISSUER", "CUSTOMER", "SUPPLIER", "GOVERNMENT", "STANDARD_BODY", "INDEPENDENT_TECHNICAL", "MARKET_DATA_PROVIDER", "THIRD_PARTY_ANALYSIS", "SOCIAL_LEAD", "SYNTHETIC"}, errors, path)
        require_enum(item, "access_class", V11_ACCESS, errors, path)
        require_enum(item, "redistribution_rights", {"ALLOWED", "NOT_ALLOWED", "UNKNOWN"}, errors, path)
        require_enum(item, "citation_status", {"CITABLE", "RESTRICTED", "UNKNOWN"}, errors, path)
        require_enum(item, "evidence_state", V11_EVIDENCE_STATES - {"UNKNOWN"}, errors, path)
        known_at = parse_v11_time(item.get("known_at"), errors, f"{path}.known_at")
        retrieved_at = parse_v11_time(item.get("retrieved_at"), errors, f"{path}.retrieved_at")
        published_at = parse_v11_time(item.get("published_at"), errors, f"{path}.published_at", required=False)
        parse_v11_time(item.get("effective_at"), errors, f"{path}.effective_at", required=False)
        parse_v11_time(item.get("effective_from"), errors, f"{path}.effective_from", required=False)
        parse_v11_time(item.get("effective_to"), errors, f"{path}.effective_to", required=False)
        require_enum(item, "time_precision", {"SECOND", "MINUTE", "DATE", "PERIOD", "UNKNOWN"}, errors, path)
        if known_at and cutoff and known_at > cutoff and item.get("evidence_state") in {"SUPPORTED", "PARTIAL"}:
            issue(errors, "temporal_leakage", path, "post-cutoff evidence cannot support this replay")
        if published_at and cutoff and published_at > cutoff and item.get("evidence_state") == "SUPPORTED":
            issue(errors, "publication_after_cutoff", path, "post-cutoff publication cannot support this replay")
        if retrieved_at and known_at and retrieved_at < known_at:
            warning(warnings, "clock_warning", path, "retrieved_at precedes known_at; verify the source clocks")

    claims_records = require_list(case.get("claims"), errors, "$.claims")
    claims = unique_ids(claims_records, "claim_id", errors, "$.claims")
    claim_link_refs: dict[str, list[str]] = {}
    referenced_evidence: set[str] = set(identity_evidence)
    for index, raw in enumerate(claims_records):
        item = require_dict(raw, errors, f"$.claims[{index}]")
        path = f"$.claims[{index}]"
        for field in ("statement", "subject", "predicate", "object", "scope"):
            require_string(item, field, errors, path, 1 if field != "statement" else 10)
        require_enum(item, "epistemic_type", V11_EPISTEMIC, errors, path)
        require_enum(item, "evidence_state", V11_EVIDENCE_STATES - {"UNKNOWN"}, errors, path)
        parse_v11_time(item.get("as_of"), errors, f"{path}.as_of")
        confidence = v11_number(item, "confidence", errors, path)
        if confidence is not None and not 0 <= confidence <= 1:
            issue(errors, "invalid_confidence", f"{path}.confidence", "confidence must be between 0 and 1")
        links = v11_ids(item, "evidence_links", errors, path)
        claim_link_refs[item.get("claim_id", "")] = links
        require_enum(item, "derivation_access", {"PUBLIC", "SYNTHETIC", "RESTRICTED", "PRIVATE", "MIXED"}, errors, path)
        derived_from = set(v11_ids(item, "derived_from_ids", errors, path, required=False))
        public_support = set(v11_ids(item, "public_support_ids", errors, path, required=False))
        referenced_evidence.update(derived_from | public_support)
        if item.get("epistemic_type") == "UNKNOWN" and item.get("evidence_state") == "SUPPORTED":
            issue(errors, "epistemic_conflict", path, "UNKNOWN claim cannot be marked SUPPORTED")
        if surface == "public" and item.get("derivation_access") in {"RESTRICTED", "PRIVATE", "MIXED"} and not public_support:
            issue(errors, "private_derivation_taint", path, "a restricted/private-derived claim needs independent public support")

    link_records = require_list(case.get("claim_evidence_links"), errors, "$.claim_evidence_links")
    links = unique_ids(link_records, "link_id", errors, "$.claim_evidence_links")
    for index, raw in enumerate(link_records):
        item = require_dict(raw, errors, f"$.claim_evidence_links[{index}]")
        path = f"$.claim_evidence_links[{index}]"
        claim_ref = require_string(item, "claim_id", errors, path)
        evidence_ref = require_string(item, "evidence_id", errors, path)
        require_enum(item, "relation", {"DIRECT_SUPPORT", "PARTIAL_SUPPORT", "CONTEXT", "CONTRADICT"}, errors, path)
        require_string(item, "support_scope", errors, path, 3)
        if claim_ref and claim_ref not in claims:
            issue(errors, "unknown_reference", f"{path}.claim_id", f"unknown claim ID: {claim_ref}")
        if evidence_ref and evidence_ref not in evidence:
            issue(errors, "unknown_reference", f"{path}.evidence_id", f"unknown evidence ID: {evidence_ref}")
        referenced_evidence.add(evidence_ref)
    link_ids = set(links)
    for claim_id, claim_links in claim_link_refs.items():
        unknown_links = sorted(link_id for link_id in claim_links if link_id not in link_ids)
        if unknown_links:
            issue(errors, "unknown_reference", f"$.claims[{claim_id}].evidence_links", f"unknown claim-evidence link IDs: {unknown_links}")
        if claims.get(claim_id, {}).get("evidence_state") == "SUPPORTED" and not claim_links:
            issue(errors, "unsupported_claim", f"$.claims[{claim_id}]", "a supported claim needs at least one evidence link")

    metrics_records = require_list(case.get("metrics"), errors, "$.metrics")
    metrics = unique_ids(metrics_records, "metric_id", errors, "$.metrics")
    for index, raw in enumerate(metrics_records):
        item = require_dict(raw, errors, f"$.metrics[{index}]")
        path = f"$.metrics[{index}]"
        for field in ("metric_name", "unit", "basis"):
            require_string(item, field, errors, path, 1)
        value = item.get("value")
        if value is not None:
            v11_number(item, "value", errors, path)
        require_enum(item, "observation_type", {"MARKET_FACT", "REGULATORY_FACT", "COMPANY_REPORTED", "CUSTOMER_REPORTED", "THIRD_PARTY_ESTIMATE", "MODEL_CALCULATION", "ASSUMPTION"}, errors, path)
        metric_sources = set(v11_ids(item, "source_ids", errors, path))
        referenced_evidence.update(metric_sources)
        if item.get("value") is None and item.get("status") not in {"UNKNOWN", "PARTIAL"}:
            issue(errors, "missing_numeric_value", path, "a null metric value must be UNKNOWN or PARTIAL")
        require_enum(item, "status", {"SUPPORTED", "PARTIAL", "STALE", "UNKNOWN", "CONTRADICTED"}, errors, path)
        parse_v11_time(item.get("published_at"), errors, f"{path}.published_at", required=False)
        parse_v11_time(item.get("known_at"), errors, f"{path}.known_at")
        parse_v11_time(item.get("effective_at"), errors, f"{path}.effective_at", required=False)
        parse_v11_time(item.get("retrieved_at"), errors, f"{path}.retrieved_at")
        require_enum(item, "time_precision", {"SECOND", "MINUTE", "DATE", "PERIOD", "UNKNOWN"}, errors, path)

    calculations_records = require_list(case.get("calculations"), errors, "$.calculations")
    calculations = unique_ids(calculations_records, "calculation_id", errors, "$.calculations")
    for index, raw in enumerate(calculations_records):
        item = require_dict(raw, errors, f"$.calculations[{index}]")
        path = f"$.calculations[{index}]"
        for field in ("calculation_type", "formula", "output_metric_id", "unit", "status"):
            require_string(item, field, errors, path, 1)
        require_enum(item, "calculation_type", {"MARKET_CAP", "ENTERPRISE_VALUE", "FX_CONVERSION", "BRIDGE_STEP", "OTHER"}, errors, path)
        require_enum(item, "status", {"REPRODUCIBLE", "PARTIAL", "UNKNOWN", "INVALID"}, errors, path)
        input_ids = set(v11_ids(item, "input_metric_ids", errors, path))
        if not input_ids:
            issue(errors, "missing_calculation_inputs", path, "a calculation must declare input metrics")
        unknown_inputs = sorted(input_ids - set(metrics))
        if unknown_inputs:
            issue(errors, "unknown_reference", f"{path}.input_metric_ids", f"unknown metric IDs: {unknown_inputs}")
        if item.get("output_metric_id") not in metrics:
            issue(errors, "unknown_reference", f"{path}.output_metric_id", "calculation output must reference a metric")

    constraints_records = require_list(case.get("constraints"), errors, "$.constraints")
    constraints = unique_ids(constraints_records, "constraint_id", errors, "$.constraints")
    referenced_constraint_evidence: set[str] = set()
    for index, raw in enumerate(constraints_records):
        item = require_dict(raw, errors, f"$.constraints[{index}]")
        path = f"$.constraints[{index}]"
        require_string(item, "label", errors, path, 3)
        dimensions = require_list(item.get("dimension_assessments"), errors, f"{path}.dimension_assessments")
        seen_dimensions: set[str] = set()
        for d_index, raw_dimension in enumerate(dimensions):
            dimension = require_dict(raw_dimension, errors, f"{path}.dimension_assessments[{d_index}]")
            d_path = f"{path}.dimension_assessments[{d_index}]"
            name = require_string(dimension, "dimension", errors, d_path, 2)
            if name in seen_dimensions:
                issue(errors, "duplicate_dimension", d_path, f"duplicate dimension: {name}")
            seen_dimensions.add(name)
            if name not in V11_DIMENSIONS:
                issue(errors, "unknown_dimension", f"{d_path}.dimension", f"unknown dimension: {name}")
            require_enum(dimension, "status", V11_EVIDENCE_STATES, errors, d_path)
            require_string(dimension, "assessment", errors, d_path, 3)
            parse_v11_time(dimension.get("as_of"), errors, f"{d_path}.as_of")
            ids = set(v11_ids(dimension, "evidence_ids", errors, d_path))
            ids.update(v11_ids(dimension, "counterevidence_ids", errors, d_path))
            referenced_constraint_evidence.update(ids)
            confidence = v11_number(dimension, "confidence", errors, d_path)
            if confidence is not None and not 0 <= confidence <= 1:
                issue(errors, "invalid_confidence", f"{d_path}.confidence", "confidence must be between 0 and 1")
            v11_ids(dimension, "unknowns", errors, d_path)
        missing_dimensions = sorted(V11_DIMENSIONS - seen_dimensions)
        if missing_dimensions:
            issue(errors, "incomplete_constraint_dimensions", f"{path}.dimension_assessments", f"missing dimensions: {missing_dimensions}")
        supply_states = require_list(item.get("supply_states"), errors, f"{path}.supply_states")
        seen_states: set[str] = set()
        for s_index, raw_state in enumerate(supply_states):
            state = require_dict(raw_state, errors, f"{path}.supply_states[{s_index}]")
            s_path = f"{path}.supply_states[{s_index}]"
            state_type = require_enum(state, "state_type", SUPPLY_STATES, errors, s_path)
            if state_type in seen_states:
                issue(errors, "duplicate_supply_state", s_path, f"duplicate supply state: {state_type}")
            seen_states.add(state_type)
            v11_number(state, "quantity", errors, s_path, required=False, allow_null=True)
            for field in ("unit", "scope", "facility_or_product", "unknowns"):
                if field == "unknowns":
                    v11_ids(state, field, errors, s_path)
                else:
                    require_string(state, field, errors, s_path, 1)
            parse_v11_time(state.get("as_of"), errors, f"{s_path}.as_of")
            require_enum(state, "epistemic_type", V11_EPISTEMIC, errors, s_path)
            require_enum(state, "evidence_state", V11_EVIDENCE_STATES - {"UNKNOWN"}, errors, s_path)
            state_evidence = set(v11_ids(state, "evidence_ids", errors, s_path))
            referenced_constraint_evidence.update(state_evidence)
            if state.get("evidence_state") == "SUPPORTED" and not state_evidence:
                issue(errors, "unsupported_supply_state", s_path, "a supported supply observation needs evidence")
        require_enum(item, "primary_state", SUPPLY_STATES, errors, path)
        require_enum(item, "status", V11_EVIDENCE_STATES - {"UNKNOWN"}, errors, path)
        top_evidence = set(v11_ids(item, "evidence_ids", errors, path))
        referenced_constraint_evidence.update(top_evidence)
        if item.get("status") == "SUPPORTED" and not top_evidence:
            issue(errors, "unsupported_constraint", path, "a supported constraint needs evidence")

    edges_records = require_list(case.get("edges"), errors, "$.edges")
    edges = unique_ids(edges_records, "id", errors, "$.edges")
    for index, raw in enumerate(edges_records):
        item = require_dict(raw, errors, f"$.edges[{index}]")
        path = f"$.edges[{index}]"
        for field in ("from", "to", "product_or_process", "relationship_type", "relationship_scope"):
            require_string(item, field, errors, path, 1)
        require_enum(item, "epistemic_type", V11_EPISTEMIC, errors, path)
        require_enum(item, "status", V11_EVIDENCE_STATES - {"UNKNOWN"}, errors, path)
        parse_v11_time(item.get("effective_from"), errors, f"{path}.effective_from", required=False)
        parse_v11_time(item.get("effective_to"), errors, f"{path}.effective_to", required=False)
        require_enum(item, "qualification_status", {"QUALIFIED", "IN_PROGRESS", "NOT_QUALIFIED", "UNKNOWN"}, errors, path)
        require_enum(item, "customer_status", {"CONFIRMED", "ISSUER_REPORTED", "INFERRED", "UNCONFIRMED", "UNKNOWN"}, errors, path)
        edge_evidence = set(v11_ids(item, "evidence_ids", errors, path))
        edge_evidence.update(v11_ids(item, "counterevidence_ids", errors, path))
        referenced_evidence.update(edge_evidence)
        v11_ids(item, "alternative_edges", errors, path)
        confidence = v11_number(item, "confidence", errors, path)
        if confidence is not None and not 0 <= confidence <= 1:
            issue(errors, "invalid_confidence", f"{path}.confidence", "confidence must be between 0 and 1")
        if item.get("status") == "SUPPORTED" and not edge_evidence:
            issue(errors, "unsupported_edge", path, "a supported dependency edge needs evidence")

    customer_records = require_list(case.get("customer_signals"), errors, "$.customer_signals")
    customer_signals = unique_ids(customer_records, "signal_id", errors, "$.customer_signals")
    for index, raw in enumerate(customer_records):
        item = require_dict(raw, errors, f"$.customer_signals[{index}]")
        path = f"$.customer_signals[{index}]"
        require_enum(item, "signal_type", {"QUALIFICATION", "DESIGN_WIN", "PURCHASE_ORDER", "REPEAT_ORDER", "LTA", "PREPAYMENT", "CAPACITY_RESERVATION", "TAKE_OR_PAY", "CUSTOMER_CAPEX_SUPPORT", "SECOND_SOURCE", "CANCELLATION", "DELAY", "OTHER"}, errors, path)
        require_enum(item, "customer_identity_status", {"NAMED", "ANONYMIZED", "UNCONFIRMED", "UNKNOWN"}, errors, path)
        require_string(item, "supplier_id", errors, path, 2)
        require_enum(item, "binding_status", {"BINDING", "NON_BINDING", "CANCELLED", "UNKNOWN"}, errors, path)
        require_string(item, "effective_period", errors, path, 2)
        signal_evidence = set(v11_ids(item, "evidence_ids", errors, path))
        referenced_evidence.update(signal_evidence)
        require_enum(item, "status", V11_EVIDENCE_STATES, errors, path)
        if item.get("status") == "SUPPORTED" and not signal_evidence:
            issue(errors, "unsupported_customer_signal", path, "a supported customer signal needs evidence")

    issuer_records = require_list(case.get("issuers"), errors, "$.issuers")
    issuers = unique_ids(issuer_records, "id", errors, "$.issuers")
    for index, raw in enumerate(issuer_records):
        item = require_dict(raw, errors, f"$.issuers[{index}]")
        path = f"$.issuers[{index}]"
        for field in ("legal_name", "ticker", "exchange", "country", "role", "capture_mechanism"):
            require_string(item, field, errors, path, 1)
        require_enum(item, "exposure_status", {"SUPPORTED", "PARTIAL", "UNKNOWN", "NOT_ESTABLISHED"}, errors, path)
        require_enum(item, "capture_status", {"SUPPORTED", "PARTIAL", "UNKNOWN", "NOT_ESTABLISHED"}, errors, path)
        issuer_evidence = set(v11_ids(item, "evidence_ids", errors, path, required=False))
        referenced_evidence.update(issuer_evidence)
        steps = require_list(item.get("capital_bridge_steps"), errors, f"{path}.capital_bridge_steps")
        # An unknown bridge is a valid incomplete research outcome, not a reason
        # to invent placeholder steps. G7 cannot PASS without verified steps.
        market = require_dict(item.get("market"), errors, f"{path}.market")
        market_path = f"{path}.market"
        require_string(market, "currency", errors, market_path, 3)
        require_enum(market, "quote_type", {"REALTIME", "DELAYED", "OFFICIAL_CLOSE", "HISTORICAL", "UNKNOWN"}, errors, market_path)
        market_status = require_enum(market, "status", {"SUPPORTED", "PARTIAL", "STALE", "UNKNOWN", "NOT_APPLICABLE"}, errors, market_path)
        price = v11_number(market, "price", errors, market_path, required=False, allow_null=True)
        shares = v11_number(market, "shares_outstanding", errors, market_path, required=False, allow_null=True)
        market_cap = v11_number(market, "market_cap", errors, market_path, required=False, allow_null=True)
        if market.get("quote_type") in {"REALTIME", "DELAYED", "OFFICIAL_CLOSE", "HISTORICAL"}:
            parse_v11_time(market.get("price_as_of"), errors, f"{market_path}.price_as_of")
        else:
            parse_v11_time(market.get("price_as_of"), errors, f"{market_path}.price_as_of", required=False)
        parse_v11_time(market.get("shares_as_of"), errors, f"{market_path}.shares_as_of", required=False)
        parse_v11_time(market.get("market_cap_as_of"), errors, f"{market_path}.market_cap_as_of", required=False)
        market_source_ids = set(v11_ids(market, "source_ids", errors, market_path))
        calculation_ids = set(v11_ids(market, "calculation_ids", errors, market_path))
        referenced_evidence.update(market_source_ids)
        unknown_calculations = sorted(calculation_ids - set(calculations))
        if unknown_calculations:
            issue(errors, "unknown_reference", f"{market_path}.calculation_ids", f"unknown calculations: {unknown_calculations}")
        if price is None or shares is None or market_cap is None:
            if market_status == "SUPPORTED":
                issue(errors, "incomplete_market_state", market_path, "a supported market state needs price, shares, and market cap")
        elif abs(price * shares - market_cap) > max(1.0, abs(market_cap) * 0.02):
            issue(errors, "market_cap_mismatch", market_path, "market cap must reconcile to price multiplied by shares")
        if market_status == "SUPPORTED" and not market_source_ids:
            issue(errors, "unsupported_market_state", market_path, "supported market state needs source IDs")

    expectation = require_dict(case.get("expectation_gap"), errors, "$.expectation_gap")
    for field in ("gap_id", "research_case", "gap_mechanism", "observable_resolution"):
        require_string(expectation, field, errors, "$.expectation_gap", 3)
    require_enum(expectation, "market_anchor_type", {"CONSENSUS_REVENUE", "CONSENSUS_MARGIN", "GUIDANCE", "VALUATION_MULTIPLE", "OPTIONS_IMPLIED", "MARKET_CAP", "EV", "PEER_IMPLIED", "UNKNOWN"}, errors, "$.expectation_gap")
    require_enum(expectation, "status", {"SUPPORTED", "PARTIAL", "UNKNOWN", "NOT_ESTABLISHED"}, errors, "$.expectation_gap")
    parse_v11_time(expectation.get("anchor_as_of"), errors, "$.expectation_gap.anchor_as_of", required=False)
    expectation_sources = set(v11_ids(expectation, "anchor_source_ids", errors, "$.expectation_gap"))
    expectation_sources.update(v11_ids(expectation, "evidence_ids", errors, "$.expectation_gap"))
    referenced_evidence.update(expectation_sources)
    if expectation.get("market_anchor_type") == "UNKNOWN" and expectation.get("status") == "SUPPORTED":
        issue(errors, "unsupported_expectation", "$.expectation_gap", "an UNKNOWN market anchor cannot support an expectation gap")

    geo = require_dict(case.get("geo_policy_risk"), errors, "$.geo_policy_risk")
    for field in ("risk_id", "assessment"):
        require_string(geo, field, errors, "$.geo_policy_risk", 3)
    require_enum(geo, "status", {"SUPPORTED", "PARTIAL", "UNKNOWN", "NOT_ESTABLISHED"}, errors, "$.geo_policy_risk")
    referenced_evidence.update(v11_ids(geo, "evidence_ids", errors, "$.geo_policy_risk"))

    reflexivity = require_dict(case.get("reflexivity_audit"), errors, "$.reflexivity_audit")
    for field in ("publicity_originated", "publication_precedes_price_move", "liquidity_state", "volume_discontinuity", "independent_fundamental_confirmation", "price_action_independent", "status"):
        require_string(reflexivity, field, errors, "$.reflexivity_audit", 1)
    for field, choices in {
        "publicity_originated": {"YES", "NO", "UNKNOWN"},
        "publication_precedes_price_move": {"YES", "NO", "UNKNOWN"},
        "liquidity_state": {"HIGH", "MEDIUM", "LOW", "UNKNOWN"},
        "volume_discontinuity": {"YES", "NO", "UNKNOWN"},
        "independent_fundamental_confirmation": {"YES", "NO", "PARTIAL", "UNKNOWN"},
        "price_action_independent": {"YES", "NO", "UNKNOWN"},
        "status": {"SUPPORTED", "PARTIAL", "UNKNOWN", "NOT_ESTABLISHED"},
    }.items():
        require_enum(reflexivity, field, choices, errors, "$.reflexivity_audit")
    referenced_evidence.update(v11_ids(reflexivity, "evidence_ids", errors, "$.reflexivity_audit"))

    countercase_records = require_list(case.get("countercases"), errors, "$.countercases")
    countercases = unique_ids(countercase_records, "id", errors, "$.countercases")
    for index, raw in enumerate(countercase_records):
        item = require_dict(raw, errors, f"$.countercases[{index}]")
        path = f"$.countercases[{index}]"
        severity = require_enum(item, "severity", SEVERITIES, errors, path)
        require_string(item, "claim", errors, path, 5)
        require_enum(item, "status", V11_EVIDENCE_STATES, errors, path)
        referenced_evidence.update(v11_ids(item, "evidence_ids", errors, path))
        plan_ids = v11_ids(item, "disproof_plan_ids", errors, path)
        if severity in {"MATERIAL", "FATAL"} and not plan_ids:
            issue(errors, "missing_disproof", path, "material and fatal countercases need a disproof plan")

    plan_records = require_list(case.get("disproof_plans"), errors, "$.disproof_plans")
    plans = unique_ids(plan_records, "id", errors, "$.disproof_plans")
    for index, raw in enumerate(plan_records):
        item = require_dict(raw, errors, f"$.disproof_plans[{index}]")
        path = f"$.disproof_plans[{index}]"
        target = require_string(item, "target_claim_id", errors, path)
        if target and target not in claims:
            issue(errors, "unknown_reference", f"{path}.target_claim_id", f"unknown claim ID: {target}")
        for field in ("observable", "threshold", "time_window", "effect_on_case"):
            require_string(item, field, errors, path, 1 if field == "threshold" else 3)

    transition_records = require_list(case.get("transitions"), errors, "$.transitions")
    transitions = unique_ids(transition_records, "id", errors, "$.transitions")
    transition_times: list[datetime] = []
    for index, raw in enumerate(transition_records):
        item = require_dict(raw, errors, f"$.transitions[{index}]")
        path = f"$.transitions[{index}]"
        require_enum(item, "from", CASE_STATES, errors, path)
        require_enum(item, "to", CASE_STATES, errors, path)
        occurred_at = parse_v11_time(item.get("occurred_at"), errors, f"{path}.occurred_at")
        if occurred_at:
            transition_times.append(occurred_at)
        require_string(item, "reason", errors, path, 3)
        referenced_evidence.update(v11_ids(item, "trigger_evidence_ids", errors, path))
        require_string(item, "case_version", errors, path, 1)
        if item.get("from") == item.get("to"):
            issue(errors, "no_op_transition", path, "a transition must change state")
        if index and transition_records[index - 1].get("to") != item.get("from"):
            issue(errors, "transition_chain", path, "each transition must start at the prior transition's destination")
    if any(transition_times[index] < transition_times[index - 1] for index in range(1, len(transition_times))):
        issue(errors, "transition_time_order", "$.transitions", "transition timestamps must be monotonic")

    current_state = require_enum(case, "current_state", CASE_STATES, errors, "$")
    classification = require_enum(case, "classification", V11_CLASSIFICATIONS, errors, "$")
    if current_state != "DRAFT" and not transitions:
        issue(errors, "missing_transition_log", "$.transitions", "non-draft cases need an append-only transition log")
    if transitions and current_state != transition_records[-1].get("to"):
        issue(errors, "transition_state_mismatch", "$.current_state", "current_state must equal the last transition destination")

    # Every public reference must resolve to a public/synthetic record.
    referenced_evidence.update(referenced_constraint_evidence)
    unknown_refs = sorted(ref for ref in referenced_evidence if ref and ref not in evidence)
    if unknown_refs:
        issue(errors, "unknown_evidence_reference", "$", f"unresolved evidence IDs: {unknown_refs}")
    _v11_public_refs(referenced_evidence, evidence, surface, errors)

    fatal_supported = any(item.get("severity") == "FATAL" and item.get("status") == "SUPPORTED" for item in countercases.values())
    if fatal_supported and current_state != "INVALIDATED":
        issue(errors, "invalidated_state_mismatch", "$.current_state", "a supported fatal countercase requires INVALIDATED")

    derived_gates = derive_gates(case)
    asserted_gates = require_dict(case.get("gates"), errors, "$.gates")
    for key in V11_GATE_KEYS:
        gate = require_dict(asserted_gates.get(key), errors, f"$.gates.{key}")
        state = require_enum(gate, "state", GATE_STATES, errors, f"$.gates.{key}")
        require_string(gate, "reason", errors, f"$.gates.{key}", 3)
        gate_refs = set(v11_ids(gate, "evidence_ids", errors, f"$.gates.{key}"))
        referenced_evidence.update(gate_refs)
        if gate_refs - set(evidence):
            issue(errors, "unknown_evidence_reference", f"$.gates.{key}", "gate evidence IDs must resolve")
        if state != derived_gates[key]["state"]:
            issue(errors, "derived_gate_mismatch", f"$.gates.{key}.state", f"asserted {state} but deterministic engine derived {derived_gates[key]['state']}")
    _v11_public_refs(referenced_evidence, evidence, surface, errors)

    derived_classification = derive_classification(derived_gates, fatal_supported)
    if classification != derived_classification:
        issue(errors, "classification_mismatch", "$.classification", f"asserted {classification} but deterministic engine derived {derived_classification}")

    return {
        "ok": not errors,
        "case_id": case_id,
        "derived_classification": derived_classification if not errors else None,
        "outcomes": research_outcomes(case, derived_gates) if not errors else None,
        "surface": surface,
        "summary": {
            "evidence": len(evidence),
            "claims": len(claims),
            "metrics": len(metrics),
            "constraints": len(constraints),
            "edges": len(edges),
            "customer_signals": len(customer_signals),
            "issuers": len(issuers),
            "countercases": len(countercases),
            "disproof_plans": len(plans),
            "gates_passed": sum(value.get("state") == "PASS" for value in derived_gates.values()),
        },
        "derived_gates": derived_gates,
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
