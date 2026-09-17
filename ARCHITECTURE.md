# Architecture

## Product shape

The project is a small compiler with four layers:

1. Intake: normalize the question, scope, cutoff, and access level.
2. Causal model: represent system shifts, dependencies, constraints, supply states, issuer exposure, capture, and capital transmission.
3. Evidence and gates: attach provenance, temporal validity, independence, uncertainty, and ordered gate decisions.
4. Report and evaluation: compile the case, expose unknowns, run disproof tests, and validate the public surface.

## Core objects

- ResearchCase: the complete dated investigation.
- SystemShift: the external change that creates or enlarges a dependency.
- DependencyMap: directed links between processes, inputs, outputs, customers, and alternatives.
- DependencyEdge: one claim that a source, process, or issuer is required or advantaged.
- ConstraintNode: a bottleneck candidate with necessity, friction, state, and evidence.
- SupplyState: the observed state of capacity, never an inferred ladder.
- IssuerProfile: the company or instrument’s role and direct exposure.
- CapturePath: the mechanism by which system value becomes issuer economics.
- CapitalBridge: the path from operating change to cash flow, funding, dilution, and per-share value.
- MarketState: dated price, shares, market value, valuation basis, and expectations.
- ExpectationGap: the difference between market-implied and research-implied outcomes.
- Countercase: a failure mode with severity, evidence, and response.
- DisproofPlan: a measurable test for a countercase or thesis claim.
- EvidenceLedger: the provenance table for every material assertion.
- CaseTransition: an immutable state change with a reason and trigger.

## State machines

### Case

    DRAFT -> EVIDENCE_BUILDING -> TESTABLE -> SUPPORTED -> STRENGTHENED
                                                    |-> WEAKENED
                                                    |-> REVISED
                                                    |-> INVALIDATED
                                                    |-> CLOSED

No state can be skipped without a transition record. INVALIDATED and CLOSED are terminal for the current case version.

### Evidence

    NOT_ESTABLISHED -> PARTIAL -> SUPPORTED
                    \-> STALE
                    \-> CONTRADICTED

New evidence creates a new ledger entry; it does not silently rewrite the old record.

### Gate

Each gate is evaluated independently, but downstream promotion is ordered:

    G0 -> G1 -> G2 -> G3 -> G4 -> G5 -> G6 -> G7

Inspection may be parallel; PASS is not. The first failed prerequisite limits the public classification.

## Causal separation

The compiler keeps four questions separate:

1. Is the system change real?
2. Is the dependency or constraint necessary?
3. Is the issuer exposed to it?
4. Can the issuer retain the economics?

An issuer can have high exposure and low capture. A constraint can be real and still be a poor investment if alternatives, price caps, or dilution absorb the value.

## Temporal semantics

Every source has at least three clocks:

- published_at: when the source became public;
- known_at: when the fact was knowable to the research process;
- retrieved_at: when the system collected it.

For replay, known_at must be on or before research_cutoff. For a live view, retrieved_at and as_of are shown. An evidence record with an unknown clock is UNKNOWN, not silently current.

## Access semantics

Access levels are PUBLIC, RESTRICTED, PRIVATE, and SYNTHETIC. An overlay may preserve the claim ID, hash, source type, and access level without exposing the source body. Public compilation excludes restricted and private evidence and reports the resulting uncertainty.

## Evaluation

The evaluation suite tests temporal leakage, unsupported supply promotion, gate compensation, market arithmetic, private-source taint, countercase completeness, provenance, adversarial prompts, and output hygiene. Quality is measured by invariant violations and human auditability, not by report length.
