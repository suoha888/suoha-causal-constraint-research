# Temporal contract (v1.1)

The compiler distinguishes four clocks:

- `published_at`: when the source was released;
- `known_at`: when the fact could have entered the research set;
- `effective_at` or an effective period: the real-world date or period described;
- `retrieved_at`: when the system collected it.

Every populated date-time includes an explicit timezone. For a replay with cutoff `C`:

```text
usable supporting evidence = known_at <= C
```

Later price moves, orders, acquisitions, or filings may update a later case version but cannot rewrite the evidence state of the earlier replay. Current market values always show quote type and retrieval time; `current` without a timestamp is invalid.

Freshness is claim-specific: quotes can expire in minutes, capacity when a project or contract changes, and audited financials at the next reporting event. Do not invent a universal freshness window.
