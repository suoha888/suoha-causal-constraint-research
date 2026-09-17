# Temporal contract

The compiler distinguishes three clocks:

- published_at: when the source was released;
- known_at: when the fact could have entered the research set;
- retrieved_at: when the system collected it.

For a replay with cutoff C:

    usable = known_at <= C

If known_at is absent or malformed, the evidence is UNKNOWN. If known_at is after C, it may be stored for a later version but cannot support the replay. A publication date after C is also excluded unless the case explicitly records an earlier knowable event and explains the discrepancy.

Live reports still show the retrieval time. “Current” without a timestamp is invalid.

## Freshness

Freshness is claim-specific. Price and market value may expire within minutes; capacity and qualification may expire when a project, contract, or process changes; audited financials expire at the next reporting event. Store a freshness window only when the analyst can defend it.
