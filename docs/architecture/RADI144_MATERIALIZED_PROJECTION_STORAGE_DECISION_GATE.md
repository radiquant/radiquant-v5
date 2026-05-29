# Radi144 Materialized Projection Storage Decision Gate

Status: materialized_projection_storage_deferred_on_demand_projection_only.

## Decision

This gate records a conservative no-go for materialized projection storage.

Current projection reads remain on-demand: the classified result endpoint reads `module_results.result_payload_json` and builds a role-safe projection with `Radi144ProjectionBuilder`. This keeps a single source of truth and avoids stale client/therapist projection copies.

## Opened scope

- Decision contract only.
- Manifest records that materialized projection storage was evaluated.
- API read projections remain enabled and on-demand.

## Still blocked

- `module_projections` table or equivalent storage
- projection payload JSON columns
- projection cache entities
- projection write service
- worker projection materialization
- raw/debug/internal projection storage

## Safety invariants

- No materialized projection table.
- No projection write service.
- No worker projection materialization.
- No raw/debug/internal projection storage.
- API read projection remains on-demand.
- Stored result payload remains source of truth.
- Future storage requires tenant/role checks and cache invalidation policy first.

## Required future gate

`radi144_projection_cache_policy_gate_decision` must exist before any materialized projection storage, cache, write service, or migration is introduced.

That future gate must define:

- cache invalidation policy
- role-specific projection freshness rules
- tenant and role authorization checks
- retention and deletion behavior
- raw/debug/internal field exclusion checks
- rebuild/idempotency behavior

## Verification

Run:

```bash
make verify
```
