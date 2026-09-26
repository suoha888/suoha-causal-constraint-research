# Architecture

## Product shape

The project is a research compiler with five layers:

1. **Identity and capability** — resolve the security and declare available data.
2. **Evidence and claims** — preserve source perspective, independence, four clocks, rights, and claim/evidence links.
3. **Causal constraint graph** — model system shifts, dependency edges, alternatives, 13 constraint dimensions, parallel supply states, and customer signals.
4. **Issuer economics** — model exposure, capture, financial transmission, market state, calculations, and expectation gaps.
5. **Gates and report** — derive deterministic gates, preserve case transitions, compile unknowns and disproof tests.

## Canonical graph

```text
SecurityIdentity
      ↓
DataAvailabilityManifest → SourceRecord → Claim ↔ ClaimEvidenceLink
      ↓                                  ↓
SystemShift → DependencyEdge → ConstraintAssessment → SupplyStateObservation
                                      ↓                    ↓
                              CustomerSignal → IssuerProfile
                                                    ↓
                                    CapitalBridge → MarketState
                                                    ↓
                                      ExpectationGap / ReflexivityAudit
                                                    ↓
                                      Countercase / DisproofPlan
```

There is one canonical schema per object. `research-case-v1.1.schema.json` composes those schemas; it does not duplicate a weaker embedded definition.

## Causal discipline

Keep these questions separate:

1. Is the system change real?
2. Is the dependency necessary and difficult to bypass?
3. Is the supplier/customer edge real and qualified?
4. Is the issuer exposed to the edge?
5. Can the issuer retain the economics after alternatives, capex, working capital, financing, and dilution?
6. Is the market expectation observably different from the research case?
7. What would prove the case wrong?

Strategic importance does not imply shareholder value. Exposure does not imply capture. A price move does not imply independent validation.

## State semantics

The seven supply labels are parallel facts, not a state machine:

```text
NAMEPLATE | INSTALLED | OPERABLE | QUALIFIED | MERCHANT | CAPTIVE | UNCOMMITTED_AVAILABLE
```

The case state machine remains append-only. Corrections create a new transition and never rewrite what was knowable at an earlier cutoff.

## Gate semantics

`scripts/gate_engine.py` derives eleven candidate-thesis support gates after schema and semantic validation. Dependencies are local: identity -> edges; necessity + edges + bypass -> constraint; edges + customers -> capture; capture -> transmission; identity + transmission -> expectations. Policy and reflexivity facts do not disappear merely because valuation is unknown. Classification is a legacy support-path label, not report quality. Invalid contracts have no trustworthy derived classification. Separate outcomes disclose coverage, evidence sufficiency, thesis state and the boundary of valuation judgment.

## Runtime boundary

The public runtime provides the contract and validation behavior. It does not grant market-data entitlements. A live adapter must satisfy `contracts/data-availability.md`, expose the source and time fields, and fail closed to `UNKNOWN` when it cannot verify freshness or rights.
