# Functional Specification

## Purpose

Implement a reusable research compiler that converts a dated research question into an auditable causal case. The implementation must be independent of any particular analyst, publication, company, or source collection.

## Input contract

A case is JSON with these required top-level fields:

- schema_version: string, currently 1;
- case_id: stable lowercase identifier;
- as_of: date on which the live view is stated;
- research_cutoff: last date whose information may affect a replay;
- question: one falsifiable decision question;
- system_shift: one material change in demand, process, policy, technology, or system design;
- constraints: candidate constraint nodes;
- edges: dependency edges between system objects;
- issuers: companies or instruments exposed to the causal chain;
- evidence: evidence ledger;
- gates: ordered gate states;
- countercases: serious ways the thesis can fail;
- disproof_plans: executable tests for countercases.

The public compiler may accept a private evidence overlay only when the overlay carries an access label. Private content is never emitted to a public report.

## Epistemic labels

- FACT: directly supported by a traceable source;
- INFERENCE: a reasoned connection supported by one or more facts;
- HYPOTHESIS: a proposed explanation or forward-looking claim;
- UNKNOWN: not established;
- CONTRADICTED: evidence materially conflicts with the claim.

## Evidence states

- SUPPORTED: current evidence supports the linked claim;
- PARTIAL: some but not all required elements are supported;
- STALE: the evidence has expired for the requested cutoff or live view;
- CONTRADICTED: material evidence points the other way;
- NOT_ESTABLISHED: a source exists but does not establish the claim.

## Ordered gates

G0 Identity & Time  
G1 Dependency Necessity  
G2 Constraint Reality  
G3 Edge Verification  
G4 Capture Proof  
G5 Financial Transmission  
G6 Expectation Test  
G7 Disproof Readiness

Gate states are PASS, PARTIAL, UNKNOWN, STALE, FAIL, and CONTRADICTED. A downstream gate can be inspected while an earlier gate is unresolved, but it cannot be reported as PASS until all prerequisites pass.

## Supply state

Use one of:

NAMEPLATE, INSTALLED, OPERABLE, QUALIFIED, MERCHANT, CAPTIVE, UNCOMMITTED_AVAILABLE.

These describe different facts. Nameplate capacity is not proof of operable output; operable output is not proof of qualification; qualification is not proof of merchant availability; captive supply is not uncommitted supply.

## Classification

- MAP_ONLY: the system is mapped but the constraint is not established;
- CONSTRAINT_CASE: a constraint is supported but issuer economics are not bridged;
- OPERATING_CASE: an issuer exposure and operating transmission are supported;
- VARIANT_CASE: the operating case differs materially from market expectations;
- RESEARCH_READY: all gates pass and the disproof plan is actionable;
- INVALIDATED: a fatal countercase is supported.

## Invariants

1. Every material claim has one or more evidence IDs or is explicitly UNKNOWN.
2. Every evidence ID is unique and resolvable.
3. Every evidence record has source type, locator, publication or known-at timing, retrieval time, access, and independence group.
4. Evidence known after research_cutoff cannot support a replay.
5. A private or restricted record cannot be used by a public surface.
6. A dependency edge cannot be SUPPORTED without evidence.
7. A QUALIFIED, MERCHANT, or UNCOMMITTED_AVAILABLE supply state cannot be inferred solely from NAMEPLATE or INSTALLED.
8. A company capture claim cannot pass without an exposure path and economic mechanism.
9. A market-cap value must reconcile to price × shares within the declared tolerance.
10. A downstream PASS is invalid when any prerequisite is not PASS.
11. Every material or fatal countercase has a disproof plan.
12. Case transitions record the prior state, new state, timestamp, reason, and triggering evidence IDs.

## Report contract

The compiler emits:

1. Research Context
2. Executive Finding
3. System Shift
4. Dependency Map
5. Constraint Assessment
6. Company / Issuer Exposure
7. Capture Path
8. Financial & Capital Bridge
9. Market Expectation Gap
10. Countercase
11. Disproof Plan
12. Unknowns & Next Checks
13. Evidence Ledger

Every number has units, currency when relevant, an as-of date, and a source link or locator. Every conclusion includes confidence, classification, and promotion or invalidation conditions.
