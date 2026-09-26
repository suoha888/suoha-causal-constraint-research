# Evidence contract (v1.1)

An evidence record is a dated source observation. It is not itself a claim and does not carry a `supports` boolean.

Required fields:

- `evidence_id`, source type, locator, and source perspective;
- `published_at`, `known_at`, `effective_at` or an effective period, `retrieved_at`, and time precision;
- `access_class`: `PUBLICLY_ACCESSIBLE`, `RESTRICTED_ACCESS`, `PRIVATE`, or `SYNTHETIC`;
- `redistribution_rights` and `citation_status`;
- `independence_group` and evidence state.

Claims link to evidence through `ClaimEvidenceLink` with `DIRECT_SUPPORT`, `PARTIAL_SUPPORT`, `CONTEXT`, or `CONTRADICT`. Repeated reports from one origin remain one independence group.

Source bodies are never required in the public contract. Public locators must be reproducible and legally usable for the intended output; restricted locators remain private.
