# Source adapter contract

Adapters fetch or receive source records; they do not decide the thesis.

An adapter must:

1. accept a source locator and retrieval timestamp;
2. return normalized metadata and a stable raw-content hash;
3. preserve publication, known-at, and retrieval clocks;
4. declare source type, access level, and independence group;
5. never infer a supply state from a marketing label;
6. return an explicit error or UNKNOWN when a field cannot be resolved;
7. keep credentials and provider-specific caches outside the public bundle.

The core compiler consumes the normalized record and applies gate rules. An adapter cannot bypass the public/private boundary.
