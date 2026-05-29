# Radi144 Materialized Projection ORM Model Decision Gate

Status: orm_model_decision_recorded_model_disabled.

## Decision

This gate records the planned ORM model boundary for future materialized projections while keeping the model disabled.

No SQLAlchemy model, Alembic migration, database table, write service, worker materialization, or new runtime route is opened in this gate.

## Planned model

- Model: `ModuleProjection`
- Table: `module_projections`

## Required future relationships

- `ModuleProjection.tenant_id_to_tenants`
- `ModuleProjection.module_run_id_to_module_runs`
- `ModuleProjection.module_result_id_to_module_results`

## Required future constraints

- tenant ID required
- role limited to `client` and `therapist`
- unique active projection per `module_result_id` and role
- raw/debug columns forbidden
- source result hash required

## Still blocked

- materialized projection ORM model
- Alembic projection migration
- materialized projection storage table
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_relationship_contract_gate_decision` must exist before any SQLAlchemy model is introduced.

## Verification

Run:

```bash
make verify
```
