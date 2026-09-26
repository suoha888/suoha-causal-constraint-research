# Calculation and numeric provenance contract

Numbers are claims, not decoration. A calculation record names its formula, input metric IDs, output metric ID, unit, and status. A calculation is `REPRODUCIBLE` only when every input is present, dated, and traceable to an allowed source.

Calculations must preserve the difference between:

- reported values;
- independently verified values;
- model inferences;
- assumptions;
- values that remain unknown.

Market capitalization, enterprise value, FX conversion, bridge steps, and per-share economics all use this contract. A report must expose the ledger instead of presenting an unexplained aggregator number.

Release 1.2 recomputes arithmetic using only declared metric IDs and +, -, *, /. It does not use eval. Market cap additionally checks current-share units and common effective time; basic EV checks market cap + debt - cash in one currency. An older share count needs a documented corporate-action reconciliation before it is treated as current; otherwise lower confidence rather than silently relabeling the old date. General formulas are arithmetic checks only. FX is intentionally not certified REPRODUCIBLE until conversion direction and units are implemented. Non-GAAP FCF and extended EV definitions must disclose adjustments. A modeled output that uses assumed inputs remains an assumption.
