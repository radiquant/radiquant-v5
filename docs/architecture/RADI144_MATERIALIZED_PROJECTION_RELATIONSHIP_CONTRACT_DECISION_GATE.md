# Radi144 Materialized Projection Relationship Contract Decision Gate

Status: relationship_contract_recorded_model_disabled.

## Decision

This gate records the future relationship contract for `ModuleProjection` while keeping the ORM model disabled.

No SQLAlchemy model, Alembic migration, database table, write service, worker materialization, or new runtime route is opened in this gate.

## Planned relationships

- `module_projections.tenant_id -> tenants.id` with `RESTRICT`
- `module_projections.module_run_id -> module_runs.id` with `CASCADE`
- `module_projections.module_result_id -> module_results.id` with `CASCADE`

## Planned constraints

- tenant ID required
- module run ID required
- module result ID required
- role limited to `client` and `therapist`
- source result hash required
- unique active projection per module result and role

## Still blocked

- materialized projection ORM model
- Alembic projection migration
- materialized projection storage table
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_constraints_gate_decision` must exist before the ORM model is introduced.

## Verification

Run:

```bash
make verify
```
