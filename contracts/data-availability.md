# Data availability contract

The skill must declare what data it can actually access before making a ticker-level claim. A research report may contain a dated close, a delayed quote, or `UNKNOWN`; it must never label an unavailable value as live.

Each adapter declares:

- `adapter_id`, provider, supported markets and capabilities;
- availability: `AVAILABLE`, `DEGRADED`, `AUTH_REQUIRED`, `UNAVAILABLE`, or `NOT_SUPPORTED`;
- latency class: `REALTIME`, `DELAYED`, `END_OF_DAY`, `BATCH`, or `UNKNOWN`;
- entitlement status and last successful retrieval;
- freshness policy and the last error when degraded.

Minimum capabilities are `SECURITY_IDENTITY`, `REALTIME_QUOTE`, `DELAYED_QUOTE`, `HISTORICAL_OHLCV`, `CORPORATE_ACTIONS`, `FILINGS`, `FUNDAMENTALS`, `GUIDANCE`, `TRANSCRIPT`, `FX`, `CONSENSUS`, `PATENT`, `POLICY`, and `CONTRACT_DISCLOSURE`.

The public runtime currently provides the contract and validators, not a market-data license or guaranteed live feed. A missing adapter produces an explicit `UNKNOWN` field and a lower research classification.
