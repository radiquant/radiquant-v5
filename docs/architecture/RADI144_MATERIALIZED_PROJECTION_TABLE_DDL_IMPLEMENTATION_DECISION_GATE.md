# Radi144 Materialized Projection Table DDL Implementation Decision Gate

Status: ddl_implementation_decision_recorded_no_ddl.

## Decision

This gate records that DDL implementation for `module_projections` remains deferred until an explicit Alembic revision gate.

No Alembic revision, `module_projections` database table, SQLAlchemy model, projection write service, worker materialization, or new runtime route is opened in this gate.

## Why DDL remains deferred

The table contract is recorded, but DDL should only be introduced after the revision identity, upgrade/downgrade test plan, partial unique index strategy, JSON column strategy, and cross-database compatibility are reviewed together.

## Required DDL implementation preconditions

- Table contract decision recorded.
- Alembic revision id reserved.
- Upgrade/downgrade test plan defined.
- SQLite and PostgreSQL compatibility reviewed.
- Partial unique index strategy reviewed.
- JSON column type strategy reviewed.
- Foreign-key ordering reviewed.
- ORM model still blocked.
- Projection write service still blocked.

## Still blocked

- Alembic projection migration
- `module_projections` database table
- materialized projection ORM model
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_alembic_revision_gate_decision` must exist before an Alembic revision file or `module_projections` DDL is introduced.

## Verification

Run:

```bash
make verify
```
