# Data policy

## Never commit to the public repository

- raw posts, subscription text, screenshots, paid articles, or source archives;
- personal data or private research notes;
- provider-controlled databases, exports, or caches without redistribution rights;
- raw source bodies hidden inside JSON, fixtures, logs, images, PDFs, archives, spreadsheets, or databases;
- a public claim whose only support is restricted or private material.

## Public fixtures

Use synthetic entities and project-authored values unless a benchmark explicitly permits redistribution. A private evaluation may retain opaque IDs and local metadata, but public reports must not expose local paths, restricted URLs, raw bodies, private titles, or raw content hashes.

## Rights-aware fields

Every source should carry `access_class`, `redistribution_rights`, `citation_status`, and `independence_group`. Derived claims should carry `derivation_access`, `derived_from_ids`, and `public_support_ids` so a private input cannot be laundered into an apparently public fact.

## Market data

Real-time, delayed, historical, consensus, and derived market values may have different licenses and freshness. An adapter must declare entitlement and latency. If the project cannot verify access or freshness, it must return `UNKNOWN` rather than cache or guess a value.
