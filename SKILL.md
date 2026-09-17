---
name: suoha-causal-constraint-research
description: Build an auditable, time-correct research case from a market or industrial-system change by tracing dependencies, binding constraints, supply states, issuer exposure, economic capture, capital transmission, market expectations, and disproof conditions. Use for deep company research, supply-chain analysis, thematic investing, and evidence-led updates where dates, source quality, and falsifiability matter.
---

# Suoha Causal Constraint Research

## Overview

Turn an open-ended market question into a testable causal case. The skill separates what is observed from what is inferred, prevents supply-capacity overclaims, connects operational exposure to per-share economics, and makes the strongest countercase executable.

## When to use

Use this skill when the user asks to:

- investigate a company through its customers, suppliers, production route, or bottleneck;
- explain why a business may be underappreciated or overvalued;
- compare competing supply routes, qualification status, or capacity claims;
- combine current price, market value, filings, operating metrics, and dated news;
- refresh a thesis with new evidence or replay what was knowable at a historical cutoff;
- produce a report that another analyst can audit and try to disprove.

Do not use it for a one-line quote, a generic company description, or a trading instruction with no research question.

## Operating rules

1. Set the research cutoff before collecting evidence. For live work, state the retrieval time; for replay, do not use information known after the cutoff.
2. Label every material statement as FACT, INFERENCE, HYPOTHESIS, or UNKNOWN. A hypothesis is not promoted by repetition.
3. Give every material claim an evidence record with source type, locator, published_at, known_at, retrieved_at, access level, and independence group. If a field is unavailable, mark it UNKNOWN instead of filling it from memory.
4. Model the system first: demand or process shift, dependency map, candidate constraint, supply state, and verified dependency edge.
5. Keep supply states distinct: NAMEPLATE, INSTALLED, OPERABLE, QUALIFIED, MERCHANT, CAPTIVE, and UNCOMMITTED_AVAILABLE are not interchangeable.
6. Test necessity, qualification friction, ramp latency, yield, merchant availability, geographic or policy concentration, customer commitment, price realization, capture retention, and capital efficiency.
7. Separate issuer exposure from economic capture. Then bridge capture to revenue, gross profit, operating cash flow, capital expenditure, financing, dilution, and per-share value.
8. Run the gate sequence in order: identity/time, dependency necessity, constraint reality, edge verification, capture proof, financial transmission, expectation test, and disproof readiness. A later pass cannot repair an earlier failed prerequisite.
9. Write the countercase before the conclusion. Every material thesis claim needs a disproof test, trigger, measurement window, and owner or next action.
10. Report current price and market value only with an as-of timestamp, currency, arithmetic method, and source. Never present stale values as live values.
11. Keep private or restricted evidence out of public output. Use a private evidence overlay with stable IDs and access labels rather than copying private source material into the public bundle.
12. This is research decision support, not personalized financial advice. State uncertainty and scenario dependence.

## Workflow

### 1. Frame the question

Write one decision question, one cutoff, one unit of analysis, and one falsifiable outcome. If the request is "should I buy it?", translate it into "what must be true for the expected return to be justified, and what evidence would break it?"

### 2. Build the causal map

Record the system shift, affected process, dependency edges, alternative routes, and candidate constraint nodes. Do not start from a ticker and backfill a story.

### 3. Verify the constraint

For each node, test necessity, route-around difficulty, qualified supplier depth, qualification friction, ramp latency, yield stability, capacity observability, merchant supply, geographic or policy concentration, and customer commitment. State the supply state explicitly.

### 4. Map issuers and capture

For each issuer, distinguish direct production, enabling input, service, integration, distribution, or financing exposure. Score capture only when there is evidence for pricing, retention, scarcity, switching cost, and allocation power.

### 5. Bridge to economics

Use a dated chain:

  physical driver -> volume / price / mix / yield / utilization -> revenue -> gross profit -> operating cash flow -> capital expenditure -> funding / dilution -> per-share economics

Mark every broken link. A compelling industry story without a capture or capital bridge remains MAP_ONLY or CONSTRAINT_CASE.

### 6. Test expectations

Compare the operational case with the market state: price, shares, market value, valuation basis, consensus or observable expectations, and what is already embedded. Show both upside and disappointment paths.

### 7. Attack the case

List local, material, and fatal countercases. Attach a disproof plan to each material or fatal claim. The plan must specify the observable signal, threshold, date window, and response.

### 8. Compile the report

Return the 13-section report described in references/output-format.md plus an evidence ledger, unresolved unknowns, and next checks. Use compact tables when they improve auditability.

## Required output behavior

Always show:

- as-of and cutoff timestamps;
- a one-sentence finding with confidence and classification;
- the causal chain from system shift to issuer economics;
- the gate state and the reason for every non-PASS gate;
- current price and market value with currency and arithmetic when requested;
- at least one serious countercase and a concrete disproof test;
- facts, inferences, hypotheses, stale items, contradictions, and unknowns separately.

If evidence is insufficient, stop at the highest defensible classification and say exactly what would promote it. Do not manufacture a number, supplier status, customer commitment, or source.

## Resources

Read only the references needed for the task:

- FUNCTIONAL_SPEC.md — neutral input, gate, and output contract;
- ARCHITECTURE.md — object model, state transitions, and invariants;
- references/evidence-priority.md — source and independence discipline;
- references/research-dialogue.md — questions to ask before and during research;
- references/output-format.md — report compiler format;
- contracts/ — field-level contracts;
- schemas/ — machine-readable structures;
- scripts/validate_research_case.py — semantic validation;
- scripts/validate_public_hygiene.py — public-surface scan;
- examples/ — synthetic fixtures only.
