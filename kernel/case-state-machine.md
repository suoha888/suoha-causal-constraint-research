# Case state machine

States:

- DRAFT: question or scope is incomplete;
- EVIDENCE_BUILDING: collection and normalization are active;
- TESTABLE: claims, gates, and disproof plans are explicit;
- SUPPORTED: current evidence supports the causal chain;
- STRENGTHENED: new independent evidence increases confidence;
- WEAKENED: evidence reduces confidence but does not invalidate;
- REVISED: the causal model changed and a new version is required;
- INVALIDATED: a fatal countercase is supported;
- CLOSED: the case is archived with its final evidence cutoff.

Every transition records:

- transition ID;
- previous and new state;
- occurred_at;
- reason;
- trigger evidence IDs;
- analyst or process ID;
- case version.

The transition log is append-only. Corrections create a new transition rather than editing history.
