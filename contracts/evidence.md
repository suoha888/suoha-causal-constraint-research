# Evidence contract

An evidence record is the smallest auditable unit supporting a claim.

Required fields:

- id: unique stable identifier;
- source_type: filing, regulator, official_release, technical_document, customer_disclosure, supplier_disclosure, specialist_analysis, market_record, interview, discussion, or synthetic;
- source_locator: URL, document identifier, file reference, or synthetic locator;
- published_at: source publication time when known;
- known_at: earliest time the fact was available to the research process;
- retrieved_at: collection time;
- access: PUBLIC, RESTRICTED, PRIVATE, or SYNTHETIC;
- independence_group: origin used to avoid double-counting;
- epistemic: FACT, INFERENCE, HYPOTHESIS, UNKNOWN, or CONTRADICTED;
- status: SUPPORTED, PARTIAL, STALE, CONTRADICTED, or NOT_ESTABLISHED;
- supports: boolean;
- claim_ids: material claims linked to this record.

The source body is not part of the public contract. A locator must be reproducible for public material or be accompanied by a declared access restriction.
