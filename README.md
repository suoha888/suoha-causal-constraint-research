# Suoha Causal Constraint Research

Input a stock. Understand what the business does, whether it controls a real bottleneck, whether that advantage reaches shareholders, what the price assumes, and what could prove the thesis wrong.

这是独立开发的股票研究 Skill：输入股票，先读一页结论，再看完整 13 维卡脖子分析和可追溯证据。研究充分、逻辑成立、价格便宜是三件不同的事；没有瓶颈或证据不足也是有效结论。

## Use it in an Agent

1. Put this repository (or the verified runtime package) in a skill folder named `suoha-causal-constraint-research` recognized by your Agent. Keep its references and scripts together, not just SKILL.md.
2. Enable an authorized search/browser or market-data tool in that Agent. No particular paid connector is mandatory. Python 3.11+ and `python -m pip install -r requirements.txt` are needed only for structured validation.
3. Ask: **“用 $suoha-causal-constraint-research 研究 NVDA，先给一页结论，再给完整卡脖子分析；缺失数据明确标注，不预设值得买。”**

You do not need to write JSON. The host Agent retrieves sources and writes the report; this is not a standalone quote server or autonomous trading application. See [the workflow](references/ticker-workflow.md) and [report format](references/output-format.md).

For an explicitly limited real-source/no-quote example, see the [NVDA smoke check](docs/real-source-smoke.md). It is not a completed stock recommendation or end-to-end quality benchmark.

The public project is deliberately conservative: it does not promise live market-data access, does not invent unavailable values, and does not reduce a complex causal chain to a single investment score.

## What a ticker report answers

For a ticker, the skill first resolves the security and declares data availability. It then answers:

1. What system or architecture changed?
2. Which dependency edge is real, qualified, and difficult to bypass?
3. What are the alternative architectures, materials, suppliers, and routes?
4. Which of the 13 constraint dimensions are supported, partial, stale, contradicted, or unknown?
5. What do nameplate, installed, operable, qualified, merchant, captive, and uncommitted supply each mean here?
6. Is there independent customer validation?
7. How directly is the issuer exposed, and how much value can it capture?
8. How does the operating mechanism reach cash flow, financing, dilution, and per-share economics?
9. What do the dated price, shares, market cap, EV, and observable expectations imply?
10. What is the strongest countercase, and what future observation would invalidate the thesis?

## Strict v1.1 contract

The primary machine-readable contract is [`schemas/research-case-v1.1.schema.json`](schemas/research-case-v1.1.schema.json). It adds:

- `SecurityIdentity` and `DataAvailabilityManifest`;
- canonical `Claim` and `ClaimEvidenceLink` objects;
- four-clock `SourceRecord` and `DatedMetric` objects;
- reproducible `CalculationRecord` objects;
- a complete 13-dimension `ConstraintAssessment`;
- parallel `SupplyState` observations;
- first-class dependency edges and customer signals;
- issuer capture, market state, expectation, geography/policy, and reflexivity objects;
- eleven deterministic research gates.

The legacy v1 contract remains accepted by the validator for compatibility. New cases should use v1.1.

## Developer checks

```text
python -m pip install -r requirements.txt
python scripts/validate_research_case.py examples/synthetic-case-v1.1.json
python scripts/check_schemas.py
python scripts/validate_public_hygiene.py
python scripts/run_evals.py --verbose
python scripts/build_runtime.py
python scripts/verify_runtime.py
```

The validator uses pinned JSON Schema dependencies, offline schema resolution and separate semantic checks. The synthetic fixture contains no live company data and grants no market-data entitlement. Every accept/reject JSONL record actually runs and asserts its result.

## Research boundary

This repository contains project-authored methods, terminology, schemas, code, validators, contracts, documentation, and synthetic fixtures. Separately maintained private research inputs are not part of the public distribution. See [`RESEARCH-PROVENANCE.md`](RESEARCH-PROVENANCE.md), [`NOTICE.md`](NOTICE.md), and [`DATA_POLICY.md`](DATA_POLICY.md).

## Status and claims

This is release 1.2.0, hardening the v1.1 case contract. Existing v1.1 cases now need a `capital_bridges` array (empty when unknown); bare step names no longer establish financial transmission. Unknown market data lowers the valuation gate. See [migration and limits](docs/release-1.2.md). It should not be described as “the strongest” or “SOTA” without a public benchmark.

This project provides research decision support, not personalized investment advice. Human review remains necessary for data licensing, accounting, legal, and investment decisions.
