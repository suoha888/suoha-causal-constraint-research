# Release 1.2.0: usable research, stricter evidence

The case schema remains named 1.1; this validator profile intentionally rejects earlier permissive cases. This is not transparent backwards compatibility. Legacy v1 validation remains available for migration, not as equivalent assurance.

## Migration

- Install `requirements.txt` for Python 3.11+.
- Add `capital_bridges`, with actual step objects matching `capital-bridge.schema.json`. If unknown, use an empty array and empty issuer step references. Do not insert invented numbers to pass G7.
- Each bridge step has a `stage`. G7 requires connected VOLUME -> REVENUE -> GROSS_PROFIT -> OPERATING_CASH -> REINVESTMENT -> FINANCING -> PER_SHARE steps. Missing or assumed steps remain unresolved. This validates path coverage, not the truth of an economic mechanism.
- Fix unknown fields, nested types and date-time formatting now enforced by Draft 7.
- Ensure support links belong to the claim and contain usable DIRECT_SUPPORT evidence. Context and contradictions do not establish support. Preserve opposing evidence separately.
- Resolve every source, bridge and disproof reference. Do not use stale sources to label current conclusions SUPPORTED. Historical evidence is evaluated at the case cutoff, not today's date.
- Recompute market cap and basic EV with declared metric IDs and units. Literals or arbitrary expressions are not executable formulas. FX calculations must remain PARTIAL until unit-aware checking is implemented. General formulas being numerically reproducible does not validate their economics.
- Snapshot prices and shares must match ledger inputs, not merely multiply to the same market cap. MARKET_CAP/EV expectation anchors must agree with the selected issuer's amount and date. Qualified customer edges cannot use NOT_QUALIFIED/UNCONFIRMED states to pass. Independent customer support cannot be supplied solely by issuer self-reporting.
- Regenerate gate assertions with `derive_gates` only after correcting facts. The new graph degrades dependent conclusions, not unrelated facts. An unknown price no longer gets a full valuation PASS. Eleven unknown dimensions cannot become a fully supported constraint.
- The validator returns no classification for invalid cases. A valid result separately reports coverage, evidence sufficiency, candidate thesis and the fact that valuation attractiveness requires research judgment.

## Release boundary

This release does not add paid feeds, proprietary data entitlements, a trading engine or a claim of market leadership. It does not publish private source archives. It does not certify comprehensive source-theory fidelity or that all qualitative judgments are correct. Gates remain consistency guardrails and a conservative positive-thesis support path, not a report-quality score.

## Validation still requiring human work

Before making superiority claims, run a frozen ten-stock pilot (including non-bottleneck, weak capture, capital-intensive and missing-data cases) with the same tools/model/budget, blind review and repeated trials. Separately have five new users explain the business, constraint, capture break, price assumption and a disproof trigger. These studies are not claimed completed by automated unit tests.
