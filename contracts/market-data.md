# Market-data contract

Ticker research starts with identity resolution, not a thesis. Resolve the legal issuer, ticker, exchange, security type, primary listing, trading currency, reporting currency, and regulator identifier before collecting prices.

Every material market value is a `DatedMetric` with:

- value, unit, currency, and basis;
- observation type: market fact, regulatory fact, company-reported, estimate, model calculation, or assumption;
- `published_at`, `known_at`, `effective_at`, `retrieved_at`, and `time_precision`;
- source IDs and, where calculated, a calculation record.

For a supported market state:

```text
market_cap = price × current shares outstanding
enterprise_value = market_cap + debt - cash + preferred + minority_interest
```

The actual formula and inputs must be stored. Weighted-average diluted shares cannot silently replace current shares outstanding. If the feed is delayed, the report must say `DELAYED`; if it is unavailable, current price and dependent values are `UNKNOWN`.
