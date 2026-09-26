# Output format

Use this order for a full ticker report. Do not hide unavailable data in prose.

## 1. One-page Executive Finding

In the user's language, explain: what the company sells; where the candidate bottleneck is; the strongest supporting and opposing facts; whether value reaches per-share cash flow; what the dated price already assumes; the largest unknown; and one observable invalidation trigger. Give separate labels for evidence sufficiency, thesis validity, and valuation attractiveness. Do not lead with internal gate names. An adverse finding is not a failed research task. Keep the summary consistent with the matrix and source ledger.

## 2. Research Context & Data Availability

Ticker, legal issuer, exchange, security type, research mode, `as_of`, `research_cutoff`, retrieval time, adapter capabilities, latency, entitlement, and missing data.

## 3. Security & Issuer Identity

Primary listing, currencies, regulator identifier, business segments, customers, geography, competitors, and substitutes.

## 4. Market Snapshot & Calculations

Quote type, price, shares, market cap, EV, FX, source IDs, timestamps, formulas, input metrics, and calculation status. Use `UNKNOWN` or `NOT_APPLICABLE` explicitly.

## 5. Business & Revenue Structure

What the company actually sells, segment/revenue exposure, customer concentration, and reporting-period boundaries.

## 6. System Shift

The observed architecture, demand, process, policy, or technology change and the evidence that establishes it.

## 7. Dependency Map & Edge Verification

End demand → system → subsystem → module → device → process → material/equipment → customer. For every material edge show product/process, scope, effective period, qualification, customer status, alternatives, evidence, and counterevidence.

## 8. Alternatives & Bypass Paths

Alternative architecture, material, process, supplier, redesign, dual sourcing, vertical integration, and time/cost/qualification barriers.

## 9. Complete 13-Dimension Constraint Matrix

Show status, assessment, as-of time, evidence IDs, counterevidence IDs, confidence, and unknowns for every dimension. Never collapse the matrix into one score.

## 10. Supply-State & Customer Validation

Show separate observations for `NAMEPLATE`, `INSTALLED`, `OPERABLE`, `QUALIFIED`, `MERCHANT`, `CAPTIVE`, and `UNCOMMITTED_AVAILABLE`. Then show customer signal type, identity status, binding status, effective period, and source perspective.

## 11. Issuer Exposure & Economic Capture

Separate role and exposure from capture mechanism, pricing, retention, switching cost, allocation power, leakage, and confidence.

## 12. Financial & Capital Bridge

Physical driver → volume/price/mix/yield/utilization → revenue → gross profit → cash flow → capex/working capital → financing/dilution → per-share economics. Identify every reported, verified, inferred, assumed, and unknown step.

## 13. Market Expectation Gap

Show an observable market anchor, its date and source, the research case, gap mechanism, resolution event, and counterevidence. If consensus is unavailable, say `UNKNOWN`.

## 14. Geographic, Policy & Resilience Risk

Manufacturing/supplier/customer geography, export/import controls, sanctions, licenses, power/water/logistics, natural-disaster exposure, concentration, and policy lead time.

## 15. Reflexivity Audit

Publication timing, price-move timing, liquidity, volume discontinuity, social attention, independent fundamental event, and whether price action is independent. Price and volume alone cannot upgrade a gate.

## 16. Countercases & Disproof Plan

Local, material, and fatal failure modes. For each material/fatal case include observable, threshold, time window, source class, and effect on classification.

## 17. Unknowns & Next Checks

Rank unknowns by decision impact and name the next source or observation that can resolve each one.

## 18. Evidence & Calculation Ledgers

Claims, claim/evidence relations, source perspective, locator, rights, independence group, four clocks, metric inputs, formulas, and reproducibility status.

## Confidence rubric

- **High:** critical gates pass and independent evidence covers the causal chain.
- **Medium:** the chain is plausible but one material link, customer signal, market anchor, or capital step is partial.
- **Low:** the map is useful but necessity, edge authenticity, capture, timing, or data availability remains unresolved.
