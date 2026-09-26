# Evaluation set

The evaluation set is intentionally synthetic and behavior-focused. It tests whether the compiler:

- rejects evidence known after a replay cutoff;
- rejects a public case tainted by restricted evidence;
- rejects supply-state promotion without direct support;
- rejects a later PASS that hides an earlier failed gate;
- reconciles price, shares, and market value;
- requires disproof plans for material and fatal countercases;
- preserves UNKNOWN instead of fabricating a source or number.

Every JSONL record must name a fixture and expected accept/reject. Mutations are executable `set`/`remove` operations with a path array. Rejections must name expected error codes. Unsupported or unexecuted records fail the run; failed evaluations return a nonzero process exit code even when unit tests pass. The count reports passed assertions, not merely parsed lines.

Synthetic JSON fixtures remain offline and deterministic. Any dated public-source smoke example is clearly labeled limited research, not a full valuation or a synthetic test. Live acquisition failures and human comprehension studies must not be represented as automated successes.
