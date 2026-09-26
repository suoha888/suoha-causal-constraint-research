# Functional specification (v1.1)

## Product promise

Given a ticker or company, produce a dated, source-led research case that explains the system constraint, proves or rejects the supply-chain relationship, tests alternatives, validates customer behavior, connects issuer exposure to per-share economics, and states what remains unknown. A missing data capability lowers the classification; it never becomes an invented value.

## Required top-level objects

The strict contract is `schemas/research-case-v1.1.schema.json`. A complete case contains:

```text
ResearchRequest
SecurityIdentity
DataAvailabilityManifest
SourceRecord[]
Claim[]
ClaimEvidenceLink[]
DatedMetric[]
CalculationRecord[]
CapitalBridge[]
SystemShift
ConstraintAssessment[]
DependencyEdge[]
CustomerSignal[]
IssuerProfile[]
ExpectationGap
GeoPolicyRisk
MarketReflexivityAudit
Countercase[]
DisproofPlan[]
ResearchGate[]
CaseTransition[]
```

## Epistemic and evidence states

`FACT`, `INFERENCE`, `HYPOTHESIS`, and `UNKNOWN` describe a claim. `SUPPORTED`, `PARTIAL`, `STALE`, `CONTRADICTED`, `NOT_ESTABLISHED`, and `UNKNOWN` describe its evidence state. `CONTRADICTED` is not an epistemic type.

Evidence records describe a source observation. A claim is supported or contradicted through `ClaimEvidenceLink`; an evidence record does not carry a legacy `supports` boolean in v1.1.

## Four clocks

Every time-aware source or metric uses:

- `published_at`: when the source became public;
- `known_at`: when the research process could know it;
- `effective_at` or an effective period: what real-world period it describes;
- `retrieved_at`: when the adapter collected it.

All date-times include an explicit timezone. A replay rejects supporting evidence whose `known_at` is after `research_cutoff`.

## Data availability

An adapter declares provider, markets, capabilities, latency class, entitlement status, freshness policy, and last error. Required capabilities include security identity, quotes, historical prices, corporate actions, filings, fundamentals, guidance, FX, consensus, contracts, policy, and technical sources.

The runtime may report `REALTIME`, `DELAYED`, `OFFICIAL_CLOSE`, `HISTORICAL`, or `UNKNOWN`. `UNKNOWN` is a valid result, not a failure to hide.

## Constraint contract

Every constraint contains exactly these 13 dimension assessments:

1. `system_necessity`
2. `route_around_difficulty`
3. `qualified_supplier_depth`
4. `qualification_friction`
5. `supply_ramp_latency`
6. `yield_stability`
7. `capacity_observability`
8. `merchant_supply_availability`
9. `geographic_policy_concentration`
10. `customer_commitment`
11. `price_realization`
12. `capture_retention`
13. `capital_efficiency`

Each assessment has status, assessment text, as-of time, evidence IDs, counterevidence IDs, confidence, and unknowns. Supply is represented as parallel observations for the seven supply states; no state promotion is implicit.

## Market and calculation contract

Every material number is a `DatedMetric`. Market capitalization is calculated from price and current shares when both are available. EV is calculated only when its components are appropriate for the instrument; for financial institutions it may be `NOT_APPLICABLE` rather than forced. Every calculation stores formula, input metric IDs, output metric ID, unit, and reproducibility status.

## Gate contract

The deterministic gate sequence is:

```text
G0 identity/time/data availability
G1 system necessity
G2 dependency edge authenticity
G3 substitution/bypass
G4 supply constraint
G5 customer validation
G6 issuer exposure/capture
G7 financial transmission
G8 market expectation
G9 geographic/policy/resilience
G10 reflexivity/disproof readiness
```

The engine derives states from schema-validated canonical objects and compares them with asserted states. An asserted `PASS` cannot override a derived `UNKNOWN`, `PARTIAL`, `FAIL`, or `CONTRADICTED`. Release 1.2 uses local prerequisites rather than one global blocking ladder. Negative and incomplete research is valid; retain the full candidate assessment and explain why the constraint is rejected or unestablished. No edge or capital step needs to be invented. Report quality, thesis validity and price attractiveness are separate judgments.

## Public/private rules

Public output may use only publicly accessible or synthetic evidence. A restricted/private-derived claim needs independent public support before it can appear as a public fact. Raw source bodies, screenshots, subscription material, private paths, and private hashes remain outside this repository.
