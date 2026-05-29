# Radi144 Projection Cache Policy Decision Gate

Status: projection_cache_policy_recorded_cache_disabled.

## Decision

This gate records the cache policy boundary while keeping projection cache storage disabled.

Current projection reads remain on-demand: the classified result endpoint reads `module_results.result_payload_json` and builds a role-safe projection with `Radi144ProjectionBuilder`. No projection cache or materialized projection copy is introduced in this gate.

## Opened scope

- Decision contract only.
- Cache policy and invalidation triggers are recorded.
- API read projections remain enabled and on-demand.

## Cache policy

Current mode: `no_cache_on_demand_projection_only`.

Required invalidation triggers before any future cache/storage may open:

- result payload rewritten
- retention deleted
- consent revoked
- role policy changed
- projection builder version changed

## Still blocked

- projection cache storage
- projection cache write service
- materialized projection storage
- worker projection materialization
- raw/debug/internal projection cache
- new projection runtime routes

## Safety invariants

- Cache storage remains disabled.
- Cache write service remains disabled.
- API read projection remains on-demand.
- Stored result payload remains source of truth.
- Future cache/storage requires tenant and role checks.
- Future cache/storage requires invalidation triggers.
- No raw/debug/internal projection cache may be stored.

## Required future gate

`radi144_materialized_projection_storage_contract_gate_decision` must exist before any materialized projection storage schema, cache table, write service, or migration is introduced.

## Verification

Run:

```bash
make verify
```
