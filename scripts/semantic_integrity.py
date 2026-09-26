"""Cross-object checks. These verify consistency, never certify source truth."""
import ast
import math
import operator
import re
from datetime import datetime


def walk(value, path="$"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def clock(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if result.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def calculate(formula, inputs):
    """Only arithmetic and declared metric IDs; no eval, functions or literals."""
    expression = formula
    names = {}
    for index, (name, metric) in enumerate(sorted(inputs.items(), key=lambda pair: -len(pair[0]))):
        alias = f"v{index}"
        expression = re.sub(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", alias, expression)
        value = metric.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("inputs must be finite numbers")
        names[alias] = value
    tree = ast.parse(expression, mode="eval")
    used = set()
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}

    def visit(node):
        if isinstance(node, ast.Name) and node.id in names:
            used.add(node.id)
            return names[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            return operations[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError("formula must use only declared metric IDs and + - * /")

    result = visit(tree.body)
    if used != set(names) or not math.isfinite(result):
        raise ValueError("all declared inputs must be used, and result must be finite")
    return result


def integrity_errors(case, surface):
    errors = []

    def fail(code, path, message):
        errors.append({"code": code, "path": path, "message": message})

    sources = {item["evidence_id"]: item for item in case["evidence"]}
    metrics = {item["metric_id"]: item for item in case["metrics"]}
    claims = {item["claim_id"]: item for item in case["claims"]}
    links = {item["link_id"]: item for item in case["claim_evidence_links"]}
    calculations = {item["calculation_id"]: item for item in case["calculations"]}
    cutoff = clock(case["research_cutoff"])
    steps = {}
    for bridge in case.get("capital_bridges", []):
        for step in bridge["steps"]:
            if step["step_id"] in steps:
                fail("duplicate_bridge_step", "$.capital_bridges", step["step_id"])
            steps[step["step_id"]] = step

    def usable(ref):
        source = sources.get(ref, {})
        known = clock(source.get("known_at"))
        return (source.get("evidence_state") == "SUPPORTED" and known is not None
                and cutoff is not None and known <= cutoff
                and (surface != "public" or (source.get("access_class") in {"PUBLICLY_ACCESSIBLE", "SYNTHETIC"}
                     and source.get("citation_status") == "CITABLE")))

    source_keys = {"evidence_ids", "counterevidence_ids", "source_ids", "anchor_source_ids",
                   "trigger_evidence_ids", "derived_from_ids", "public_support_ids"}
    for path, item in walk(case):
        for field, number in item.items():
            if isinstance(number, float) and not math.isfinite(number):
                fail("nonfinite_number", path + "." + field, "Numbers must be finite")
        for field in source_keys:
            for ref in item.get(field, []):
                if ref not in sources:
                    fail("unknown_evidence_reference", path + "." + field, f"Unknown source: {ref}")
                elif surface == "public" and (sources[ref].get("access_class") not in {"PUBLICLY_ACCESSIBLE", "SYNTHETIC"}
                                               or sources[ref].get("citation_status") != "CITABLE"):
                    fail("private_evidence_taint", path + "." + field, f"Not publicly citable: {ref}")
        for field in ("price_source_id", "shares_source_id"):
            ref = item.get(field)
            if ref is not None and ref not in sources:
                fail("unknown_evidence_reference", path + "." + field, str(ref))
        state = item.get("status", item.get("evidence_state"))
        refs = item.get("evidence_ids", item.get("source_ids"))
        if item.get("input_type") in {"REPORTED", "VERIFIED"} and not any(usable(ref) for ref in item.get("evidence_ids", [])):
            fail("unsupported_bridge_evidence", path, "Reported or verified bridge steps require usable evidence")
        if state == "SUPPORTED" and refs is not None and not any(usable(ref) for ref in refs):
            fail("unsupported_evidence", path, "SUPPORTED requires at least one usable supporting source, not only stale or negative evidence")
        for field in ("known_at", "published_at", "price_as_of", "shares_as_of", "market_cap_as_of", "enterprise_value_as_of", "anchor_as_of"):
            when = clock(item.get(field))
            if when and cutoff and when > cutoff:
                fail("temporal_leakage", path + "." + field, "Observation is later than research cutoff")
        observation = clock(item.get("as_of"))
        if path != "$" and observation and cutoff and observation > cutoff:
            fail("temporal_leakage", path + ".as_of", "Observation is later than research cutoff")
        start, end = clock(item.get("effective_from")), clock(item.get("effective_to"))
        if start and end and start > end:
            fail("effective_time_order", path, "effective_from exceeds effective_to")
        if state == "SUPPORTED" and ((start and cutoff and start > cutoff) or (end and cutoff and end < cutoff)):
            fail("outside_effective_period", path, "Relationship is not active at cutoff")

    for index, claim in enumerate(case["claims"]):
        path = f"$.claims[{index}]"
        owned = []
        for key in ("evidence_links", "counterevidence_links"):
            for ref in claim.get(key, []):
                link = links.get(ref)
                if not link or link["claim_id"] != claim["claim_id"]:
                    fail("link_ownership", path, f"Link {ref} does not belong to this claim")
                elif key == "evidence_links":
                    owned.append(link)
        if claim["evidence_state"] == "SUPPORTED" and not any(link["relation"] == "DIRECT_SUPPORT" and usable(link["evidence_id"]) for link in owned):
            fail("unsupported_claim", path, "SUPPORTED requires an owned DIRECT_SUPPORT link to usable evidence")
        if claim.get("derivation_access") in {"PRIVATE", "MIXED", "RESTRICTED"} and surface == "public":
            public = set(claim.get("public_support_ids", []))
            if not any(link["evidence_id"] in public and usable(link["evidence_id"]) and link["relation"] == "DIRECT_SUPPORT" for link in owned):
                fail("private_derivation_taint", path, "Public support must be directly linked to the same claim")

    for index, calc in enumerate(case["calculations"]):
        path = f"$.calculations[{index}]"
        if calc["status"] != "REPRODUCIBLE":
            continue
        try:
            inputs = {ref: metrics[ref] for ref in calc["input_metric_ids"]}
            output = metrics[calc["output_metric_id"]]
            result = calculate(calc["formula"], inputs)
            if output.get("calculation_id") != calc["calculation_id"] or calc["unit"] != output["unit"]:
                raise ValueError("output must link back to calculation and use its unit")
            if not isinstance(output["value"], (int, float)) or not math.isclose(result, output["value"], rel_tol=1e-9, abs_tol=0.01):
                raise ValueError("recomputed result does not match output")
            if any(m["status"] != "SUPPORTED" for m in inputs.values()) and output["status"] == "SUPPORTED":
                raise ValueError("uncertain inputs cannot produce a supported output")
            if any(m["observation_type"] == "ASSUMPTION" for m in inputs.values()) and output["observation_type"] != "ASSUMPTION":
                raise ValueError("assumption taint must propagate to output")
            kind = calc["calculation_type"]
            rows = list(inputs.values())
            if kind == "MARKET_CAP":
                price = [m for m in rows if m["unit"] == output["unit"] + "/share"]
                shares = [m for m in rows if m["unit"] == "shares" and m["metric_name"] == "shares_outstanding"]
                if len(rows) != 2 or len(price) != 1 or len(shares) != 1:
                    raise ValueError("market cap requires price per share and current shares, not weighted-average diluted shares")
                if not price[0].get("effective_at") or price[0]["effective_at"] != shares[0].get("effective_at") or output.get("effective_at") != price[0]["effective_at"]:
                    raise ValueError("price/share basis must be reconciled to a common effective timestamp")
                if not math.isclose(price[0]["value"] * shares[0]["value"], result, rel_tol=1e-9):
                    raise ValueError("MARKET_CAP must multiply price and shares")
            elif kind == "ENTERPRISE_VALUE":
                by_name = {m["metric_name"]: m for m in rows}
                if set(by_name) != {"market_cap", "debt", "cash"} or len(rows) != 3 or any(m["unit"] != output["unit"] or m.get("currency") != output.get("currency") for m in rows):
                    raise ValueError("basic EV requires market_cap + debt - cash in one currency; extended EV must use OTHER and disclose adjustments")
                expected = by_name["market_cap"]["value"] + by_name["debt"]["value"] - by_name["cash"]["value"]
                if not math.isclose(expected, result, rel_tol=1e-9, abs_tol=.01):
                    raise ValueError("EV signs are incorrect")
            elif kind == "FX_CONVERSION":
                raise ValueError("FX unit/basis validation is not implemented; label PARTIAL instead of REPRODUCIBLE")
        except (KeyError, ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError) as exc:
            fail("calculation_integrity", path, str(exc))

    for index, metric in enumerate(case["metrics"]):
        ref = metric.get("calculation_id")
        if ref and (ref not in calculations or calculations[ref]["output_metric_id"] != metric["metric_id"]):
            fail("unknown_reference", f"$.metrics[{index}]", "Calculation does not produce this metric")

    issuer_ids = {item["id"] for item in case["issuers"]}
    plan_ids = {item["id"] for item in case["disproof_plans"]}
    for index, counter in enumerate(case["countercases"]):
        if set(counter["disproof_plan_ids"]) - plan_ids:
            fail("unknown_reference", f"$.countercases[{index}]", "Disproof plan ID does not resolve")
    for index, signal in enumerate(case["customer_signals"]):
        if signal["supplier_id"] not in issuer_ids:
            fail("unknown_reference", f"$.customer_signals[{index}].supplier_id", "Unknown issuer")
    for index, issuer in enumerate(case["issuers"]):
        path = f"$.issuers[{index}]"
        for ref in issuer["capital_bridge_steps"]:
            if ref not in steps:
                fail("unknown_reference", path + ".capital_bridge_steps", f"Unknown step {ref}")
        for ref in issuer.get("exposure_claim_ids", []):
            if ref not in claims:
                fail("unknown_reference", path + ".exposure_claim_ids", str(ref))
        if issuer["capture_status"] == "SUPPORTED" and not any(usable(ref) for ref in issuer.get("evidence_ids", [])):
            fail("unsupported_evidence", path, "Economic capture needs usable evidence")
        market = issuer["market"]
        if market["status"] == "SUPPORTED":
            for kind, field in (("MARKET_CAP", "market_cap"), ("ENTERPRISE_VALUE", "enterprise_value")):
                if market.get(field) is None:
                    continue
                candidates = [calculations[ref] for ref in market["calculation_ids"] if ref in calculations and calculations[ref]["calculation_type"] == kind]
                if not candidates or not any(c["status"] == "REPRODUCIBLE" and metrics.get(c["output_metric_id"], {}).get("value") == market[field] and metrics.get(c["output_metric_id"], {}).get("currency") == market["currency"] for c in candidates):
                    fail("market_ledger_mismatch", path + ".market", f"{field} must agree with a reproducible ledger output")
                if kind == "MARKET_CAP":
                    for calc in candidates:
                        rows = [metrics[ref] for ref in calc["input_metric_ids"] if ref in metrics]
                        prices = [m for m in rows if m["unit"] == market["currency"] + "/share"]
                        shares = [m for m in rows if m["metric_name"] == "shares_outstanding"]
                        if len(prices) != 1 or len(shares) != 1 or prices[0]["value"] != market.get("price") or shares[0]["value"] != market.get("shares_outstanding") or prices[0].get("effective_at") != market.get("price_as_of") or shares[0].get("effective_at") != market.get("shares_as_of"):
                            fail("market_ledger_mismatch", path + ".market", "Snapshot price, shares and their dates must agree with ledger inputs")
    anchor = case["expectation_gap"]
    if anchor["status"] == "SUPPORTED" and (not clock(anchor.get("anchor_as_of")) or not any(usable(ref) for ref in anchor["anchor_source_ids"])):
        fail("unsupported_expectation", "$.expectation_gap", "A supported expectation needs a dated, usable market anchor")
    if anchor["status"] == "SUPPORTED" and anchor["market_anchor_type"] in {"MARKET_CAP", "EV"}:
        field = "market_cap" if anchor["market_anchor_type"] == "MARKET_CAP" else "enterprise_value"
        target = next((i for i in case["issuers"] if i["id"] == case["security_identity"]["issuer_id"]), None)
        if not target or (target["market"]["status"] == "SUPPORTED" and (anchor["market_anchor_value"] != target["market"].get(field) or anchor["anchor_as_of"] != target["market"].get(field + "_as_of"))):
            fail("expectation_anchor_mismatch", "$.expectation_gap", "Anchor must equal the target issuer's dated market ledger, not another value")
    return errors


def research_outcomes(case, gates):
    """Keep contract integrity, evidence sufficiency and economic opinion separate."""
    dimensions = [d for c in case["constraints"] for d in c["dimension_assessments"]]
    supported = sum(d["status"] == "SUPPORTED" for d in dimensions)
    fatal = any(c["status"] == "SUPPORTED" and c["severity"] == "FATAL" for c in case["countercases"])
    rejected = fatal or all(c["status"] == "CONTRADICTED" for c in case["constraints"])
    return {
        "contract_integrity": "VALID",
        "dimension_coverage": f"{len(dimensions)} assessed; {supported} supported",
        "evidence_sufficiency": "COMPLETE" if all(g["state"] == "PASS" for g in gates.values()) else "PARTIAL",
        "constraint_thesis": "REFUTED" if rejected else ("CANDIDATE_SUPPORTED" if all(gates[k]["state"] == "PASS" for k in list(gates)[:8]) else "NOT_ESTABLISHED"),
        "valuation_attractiveness": "NOT_DETERMINED_BY_VALIDATOR",
        "synthetic": any(s["access_class"] == "SYNTHETIC" for s in case["evidence"]),
        "notice": "Valid negative or incomplete research is useful. Gate passage is not a buy signal or source-truth certification.",
    }
