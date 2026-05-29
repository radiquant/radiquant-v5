# Radi144 Worker Projection Materialization Decision Gate

Status: worker_projection_materialization_deferred_api_read_projection_only.

## Decision

This gate records a conservative no-go for worker-side projection materialization.

Current Radi144 projection reads are intentionally on-demand: the classified result endpoint loads the stored `module_results.result_payload_json` and passes it through `Radi144ProjectionBuilder` for the requested role. That keeps one source of truth and avoids projection drift.

## Opened scope

- Decision contract only.
- Manifest records that worker projection materialization was evaluated.
- Existing API read projection remains allowed.

## Still blocked

- worker projection builder calls
- materialized projection table/storage
- projection payload writes from worker runtime
- raw/debug/internal projection storage
- new projection runtime routes
- background projection cache refresh

## Safety invariants

- API read projection remains on-demand.
- `module_results.result_payload_json` remains the source of truth.
- Worker runtime must not import or call `Radi144ProjectionBuilder`.
- No materialized projection storage exists yet.
- No raw/debug/internal projection data may be stored.
- Tenant context remains required for projection reads.

## Required future gate

`radi144_materialized_projection_storage_gate_decision` must exist before any projection table, cache, write service, or worker materialization is introduced.

That future gate must define:

- projection storage schema
- role-specific projection payload contracts
- invalidation and rebuild policy
- tenant and role access checks
- raw/debug/internal field exclusion checks
- migration and retention policy

## Verification

Run:

```bash
make verify
```
