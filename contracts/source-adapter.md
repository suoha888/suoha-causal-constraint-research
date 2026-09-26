# Source adapter contract

Adapters fetch or receive source records; they do not decide the thesis. A market adapter also does not decide whether a value is investable or important.

An adapter must:

1. declare provider, markets, capabilities, latency class, entitlement, and freshness policy;
2. accept a source locator and retrieval timestamp;
3. return normalized metadata and an access-appropriate content reference;
4. preserve publication, effective, known-at, and retrieval clocks;
5. declare source perspective, access class, rights, citation status, and independence group;
6. never infer a supply state or customer relationship from a marketing label;
7. return an explicit error or UNKNOWN when a field cannot be resolved;
8. keep credentials, raw bodies, provider-specific caches, and restricted hashes outside the public bundle.

The core compiler consumes the normalized record and applies gate rules. An adapter cannot bypass the public/private boundary.
