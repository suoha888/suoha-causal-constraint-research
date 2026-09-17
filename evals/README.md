# Evaluation set

The evaluation set is intentionally synthetic and behavior-focused. It tests whether the compiler:

- rejects evidence known after a replay cutoff;
- rejects a public case tainted by restricted evidence;
- rejects supply-state promotion without direct support;
- rejects a later PASS that hides an earlier failed gate;
- reconciles price, shares, and market value;
- requires disproof plans for material and fatal countercases;
- preserves UNKNOWN instead of fabricating a source or number.

The checked-in examples contain no real company conclusion. Add a real case only in a separately governed research workspace.
