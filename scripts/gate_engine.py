#!/usr/bin/env python3
"""Deterministic gate derivation for the v1.1 research contract.

The engine deliberately returns UNKNOWN/PARTIAL instead of inferring missing
market or supply facts.  It is a completeness gate, not an investment score.
"""

from __future__ import annotations

from typing import Any


GATE_KEYS = [
    "G0_identity_time",
    "G1_system_necessity",
    "G2_dependency_edge",
    "G3_substitution_bypass",
    "G4_supply_constraint",
    "G5_customer_validation",
    "G6_issuer_capture",
    "G7_financial_transmission",
    "G8_market_expectation",
    "G9_geo_policy",
    "G10_reflexivity_disproof",
]

PASSABLE = {"SUPPORTED", "PASS"}
BRIDGE_STAGES = ["VOLUME", "REVENUE", "GROSS_PROFIT", "OPERATING_CASH", "REINVESTMENT", "FINANCING", "PER_SHARE"]


def independent_customer_signal(signal, sources):
    return any(sources.get(ref, {}).get("source_perspective") in {"CUSTOMER", "REGULATOR", "INDEPENDENT_TECHNICAL", "SYNTHETIC"} and sources.get(ref, {}).get("evidence_state") == "SUPPORTED" for ref in signal.get("evidence_ids", []))


def full_bridge(issuer, steps):
    path = [steps.get(ref, {}) for ref in issuer.get("capital_bridge_steps", [])]
    return ([s.get("stage") for s in path] == BRIDGE_STAGES
            and all(s.get("input_type") in {"VERIFIED", "REPORTED"} and s.get("evidence_ids") and all(s.get(k) is not None for k in ("baseline", "scenario", "unit", "period")) for s in path)
            and all(a.get("to_metric") == b.get("from_metric") for a, b in zip(path, path[1:])))


def _status(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("status", value.get("evidence_state", "UNKNOWN")))
    return "UNKNOWN"


def _has_supported(items: Any) -> bool:
    return isinstance(items, list) and any(_status(item) in PASSABLE for item in items)


def _all_supported(items: Any) -> bool:
    return isinstance(items, list) and bool(items) and all(_status(item) in PASSABLE for item in items)


def _evidence(items: Any) -> list[str]:
    result: list[str] = []
    if not isinstance(items, list):
        return result
    for item in items:
        if isinstance(item, dict):
            ids = item.get("evidence_ids", [])
            if isinstance(ids, list):
                result.extend(value for value in ids if isinstance(value, str))
    return sorted(set(result))


def derive_gates(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Derive v1.1 gate states from canonical objects.

    The returned states are intentionally conservative.  A caller may display
    asserted gate reasons, but should never override these derived states.
    """

    identity = case.get("security_identity", {})
    availability = case.get("data_availability", {})
    constraints = case.get("constraints", [])
    edges = case.get("edges", [])
    signals = case.get("customer_signals", [])
    issuers = case.get("issuers", [])
    expectation = case.get("expectation_gap", {})
    reflexivity = case.get("reflexivity_audit", {})
    plans = case.get("disproof_plans", [])
    geo = case.get("geo_policy_risk", {})
    sources = {s["evidence_id"]: s for s in case.get("evidence", [])}

    raw: dict[str, dict[str, Any]] = {}
    raw["G0_identity_time"] = {
        "state": "PASS" if _status(identity) in PASSABLE and identity.get("evidence_ids") and any(a.get("availability") == "AVAILABLE" for a in availability.get("adapters", [])) else "UNKNOWN",
        "reason": "Security identity and adapter capability manifest are explicit.",
        "evidence_ids": _evidence([identity]),
    }
    system_shift = case.get("system_shift", {})
    dimension_statuses = [
        item.get("status")
        for constraint in constraints
        if isinstance(constraint, dict)
        for item in constraint.get("dimension_assessments", [])
        if isinstance(item, dict) and item.get("dimension") == "system_necessity"
    ]
    raw["G1_system_necessity"] = {
        "state": "PASS" if _status(system_shift) in PASSABLE and dimension_statuses and all(value in PASSABLE for value in dimension_statuses) else "UNKNOWN",
        "reason": "The system shift and architecture-necessity dimension are both evidenced.",
        "evidence_ids": _evidence([system_shift]),
    }
    raw["G2_dependency_edge"] = {
        "state": "PASS" if _all_supported(edges) and all(item.get("evidence_ids") and item.get("qualification_status") == "QUALIFIED" and item.get("customer_status") == "CONFIRMED" for item in edges) else "UNKNOWN",
        "reason": "Every promoted dependency edge carries a dated relationship and evidence.",
        "evidence_ids": _evidence(edges),
    }
    bypass_statuses = [
        item.get("status")
        for constraint in constraints
        if isinstance(constraint, dict)
        for item in constraint.get("dimension_assessments", [])
        if isinstance(item, dict) and item.get("dimension") == "route_around_difficulty"
    ]
    raw["G3_substitution_bypass"] = {
        "state": "PASS" if bypass_statuses and all(value in PASSABLE for value in bypass_statuses) else "UNKNOWN",
        "reason": "Alternative routes and bypass difficulty are explicitly assessed.",
        "evidence_ids": _evidence(constraints),
    }
    supply_states = [
        state
        for constraint in constraints
        if isinstance(constraint, dict)
        for state in constraint.get("supply_states", [])
        if isinstance(state, dict)
    ]
    raw["G4_supply_constraint"] = {
        "state": "PASS" if _all_supported(constraints) and supply_states and all(_status(item) in PASSABLE for item in supply_states) and all(len(c.get("dimension_assessments", [])) == 13 and all(d.get("status") in PASSABLE for d in c["dimension_assessments"]) and {s.get("state_type") for s in c.get("supply_states", [])} == {"NAMEPLATE", "INSTALLED", "OPERABLE", "QUALIFIED", "MERCHANT", "CAPTIVE", "UNCOMMITTED_AVAILABLE"} for c in constraints) else "UNKNOWN",
        "reason": "Supply capacity is represented as parallel dated facts rather than a promoted ladder.",
        "evidence_ids": _evidence(supply_states),
    }
    raw["G5_customer_validation"] = {
        "state": "PASS" if any(_status(s) in PASSABLE and independent_customer_signal(s, sources) and s.get("signal_type") not in {"CANCELLATION", "DELAY", "SECOND_SOURCE", "OTHER"} and s.get("binding_status") != "CANCELLED" and s.get("customer_identity_status") in {"NAMED", "ANONYMIZED"} for s in signals) and not any(_status(s) in PASSABLE and (s.get("binding_status") == "CANCELLED" or s.get("signal_type") in {"CANCELLATION", "DELAY", "SECOND_SOURCE"}) for s in signals) else ("PARTIAL" if signals else "UNKNOWN"),
        "reason": "Customer validation signals are independently modeled and dated.",
        "evidence_ids": _evidence(signals),
    }
    raw["G6_issuer_capture"] = {
        "state": "PASS" if issuers and all(item.get("exposure_status") in PASSABLE and item.get("capture_status") in PASSABLE for item in issuers if isinstance(item, dict)) else "UNKNOWN",
        "reason": "Issuer exposure and economic capture are separate assertions.",
        "evidence_ids": _evidence(issuers),
    }
    verified_steps = {s["step_id"]: s for b in case.get("capital_bridges", []) if b.get("status") == "SUPPORTED" for s in b.get("steps", [])}
    raw["G7_financial_transmission"] = {
        "state": "PASS" if issuers and all(full_bridge(item, verified_steps) for item in issuers) else "UNKNOWN",
        "reason": "The operating mechanism has an explicit capital-bridge path.",
        "evidence_ids": _evidence(issuers),
    }
    raw["G8_market_expectation"] = {
        "state": "PASS" if _status(expectation) in PASSABLE and expectation.get("anchor_source_ids") and expectation.get("market_anchor_type") not in {None, "UNKNOWN"} and all(i.get("market", {}).get("status") == "SUPPORTED" for i in issuers) else ("PARTIAL" if expectation else "UNKNOWN"),
        "reason": "Market expectations are tied to an observable anchor or remain explicitly unknown.",
        "evidence_ids": _evidence([expectation]),
    }
    raw["G9_geo_policy"] = {
        "state": "PASS" if _status(geo) in PASSABLE else ("UNKNOWN" if not geo else "PARTIAL"),
        "reason": "Geographic, policy, and resilience risks are assessed separately from pricing power.",
        "evidence_ids": _evidence([geo]),
    }
    raw["G10_reflexivity_disproof"] = {
        "state": "PASS" if _status(reflexivity) in PASSABLE and plans else "UNKNOWN",
        "reason": "Reflexivity and executable disproof conditions are present.",
        "evidence_ids": _evidence([reflexivity]),
    }

    # Local dependency graph: missing valuation must not erase policy/customer facts.
    prerequisites = {"G2_dependency_edge": ["G0_identity_time"], "G4_supply_constraint": ["G1_system_necessity", "G2_dependency_edge", "G3_substitution_bypass"], "G6_issuer_capture": ["G2_dependency_edge", "G5_customer_validation"], "G7_financial_transmission": ["G6_issuer_capture"], "G8_market_expectation": ["G0_identity_time", "G7_financial_transmission"]}
    for key, dependencies in prerequisites.items():
        if raw[key]["state"] == "PASS" and any(raw[d]["state"] != "PASS" for d in dependencies):
            raw[key]["state"] = "PARTIAL"
            raw[key]["reason"] += " A required dependency is unresolved."
    return raw


def derive_classification(gates: dict[str, dict[str, Any]], fatal_countercase: bool = False) -> str:
    if fatal_countercase:
        return "INVALIDATED"
    states = [gates.get(key, {}).get("state") for key in GATE_KEYS]
    if all(state == "PASS" for state in states):
        return "RESEARCH_READY"
    if all(state == "PASS" for state in states[:9]):
        return "VARIANT_CASE"
    if all(state == "PASS" for state in states[:8]):
        return "OPERATING_CASE"
    if all(state == "PASS" for state in states[:6]):
        return "CUSTOMER_VALIDATED_CASE"
    if all(state == "PASS" for state in states[:5]):
        return "CONSTRAINT_CASE"
    return "MAP_ONLY"
