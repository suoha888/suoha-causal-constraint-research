# Suoha Causal Constraint Research

An independent, evidence-led research skill for turning a system change into a testable company or supply-chain case.

The project is organized around a simple question:

> What must be true for this market story to become durable issuer economics, and what evidence would prove it wrong?

It is designed for current research and historical replay. The public bundle contains methods, contracts, schemas, synthetic examples, validators, and build tooling. Private evidence can be connected through an access-controlled overlay without being copied into the public repository.

## What it produces

- a dated system-shift and dependency map;
- explicit constraint and supply states;
- verified dependency edges;
- issuer exposure separated from economic capture;
- a capital bridge to per-share economics;
- a market-expectation gap;
- countercases and executable disproof plans;
- an evidence ledger with provenance and uncertainty labels.

## Quick start

Validate a synthetic case:

    python scripts/validate_research_case.py examples/synthetic-case.json

Scan the public surface:

    python scripts/validate_public_hygiene.py

Build and verify the runtime manifest:

    python scripts/build_runtime.py
    python scripts/verify_runtime.py

The validator uses only the Python standard library.

## Design

The workflow is:

    question -> cutoff -> system shift -> dependency map -> constraint
    -> supply state -> edge verification -> issuer exposure -> capture
    -> capital bridge -> expectations -> countercase -> disproof -> report

The gate engine is ordered. A later PASS cannot compensate for an earlier FAIL, CONTRADICTED, UNKNOWN, or STALE prerequisite.

## Public/private boundary

Public files contain no personal research profiles, private source material, or source-dependent attribution. The private overlay contract keeps access level, provenance, and stable IDs visible to the compiler while keeping restricted content outside the public surface.

This repository provides research decision support and validation tooling. It does not provide personalized investment advice.

## Quality bar

Before release, CI must show zero public-surface hygiene violations, zero severe temporal leakage, valid schemas, no unsupported edge promotion, no gate invariant violations, and passing synthetic/adversarial fixtures. A human review remains required for legal, accounting, and investment decisions.
