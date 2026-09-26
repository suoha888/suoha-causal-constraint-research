# Constraint model

A constraint node has three layers:

1. Necessity: does the target system require this input, route, process, or capability?
2. Friction: how hard is it to route around through redesign, substitution, qualification, geography, policy, or time?
3. Supply state: what is physically and commercially true today?

## Dimensions

- system_necessity
- route_around_difficulty
- qualified_supplier_depth
- qualification_friction
- supply_ramp_latency
- yield_stability
- capacity_observability
- merchant_supply_availability
- geographic_policy_concentration
- customer_commitment
- price_realization
- capture_retention
- capital_efficiency

Record a status, assessment, as-of timestamp, evidence IDs, counterevidence IDs, confidence, and unknowns for every one of the 13 dimensions. A score without a reason is not an assessment; v1.1 does not use a single constraint score.

## State discipline

NAMEPLATE is a declared maximum. INSTALLED is equipment present. OPERABLE is equipment producing. QUALIFIED is accepted for a specified use. MERCHANT is sellable to an external buyer. CAPTIVE is reserved for the owner’s internal use. UNCOMMITTED_AVAILABLE is both operable and not committed to another use. These states can coexist for different portions of one facility.
