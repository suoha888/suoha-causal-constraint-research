# Release readiness

## Release 1.2.0 — evidence integrity and usable entrypoint

Current local status:

- strict v1.1 schema and semantic validator: passing;
- 13-dimension constraint fixture: passing;
- 11 deterministic gates: passing on the complete synthetic fixture;
- market-cap calculation reconciliation: enforced;
- unknown quote behavior: tested;
- private/restricted evidence taint: enforced;
- timezone-aware replay clocks: enforced;
- public hygiene and history scan: passing;
- runtime build and verification: passing;
- unit tests: 66 passing; final checks recorded during the 2026-09-26 session;
- executable JSONL eval records: 11 executed and asserted, including reject cases;
- independent forward test identified five additional promotion defects; all five now have regression tests;
- isolated runtime test validates the packaged fixture; corrupt files and malformed manifests are rejected;
- one real public-source/no-quote smoke check is documented; it is not full end-to-end investment research.

## Explicit limitations

This release provides contracts, validation, and synthetic behavior tests. It does not itself grant real-time quote, consensus, transcript, or proprietary-data entitlements, and it does not yet ship production market/filing adapters. A runtime without an authorized adapter must report `UNKNOWN`, `DELAYED`, or `OFFICIAL_CLOSE` according to the capability manifest.

Source truth, scope matching, accounting-model correctness and theoretical fidelity still require actual research. FX unit checking is not implemented and cannot be marked REPRODUCIBLE. The ten-stock blind pilot and five-user comprehension study have not been completed. No claim of market leadership follows from this release. Publication/remote synchronization is separate from local checks.

## Before public push

1. Review the diff and generated package contents.
2. Run CI-equivalent checks from a clean checkout.
3. Confirm no private corpus, raw source body, screenshot, or restricted locator is included.
4. Confirm data-provider terms for any future adapter.
5. Publish only after a human review of the release boundary.
