# Radi144 Materialized Projection Storage Migration Decision Gate

Status: migration_decision_recorded_migration_disabled.

## Decision

This gate records that the materialized projection migration is intentionally deferred until an ORM model gate defines the table shape in code.

No Alembic revision, ORM model, database table, write service, worker materialization, or new runtime route is opened in this gate.

## Opened scope

- Decision contract only.
- Planned migration entity remains `module_projections`.
- Preconditions for a future migration are documented.

## Required preconditions before migration

- ORM model contract reviewed.
- Tenant foreign keys defined.
- Role unique constraint defined.
- Raw/debug columns forbidden.
- Retention delete policy defined.

## Still blocked

- Alembic projection migration
- materialized projection ORM model
- materialized projection storage table
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_orm_model_gate_decision` must exist before any ORM model or Alembic migration is introduced.

## Verification

Run:

```bash
make verify
```
