# Radi144 Materialized Projection Table Creation Decision Gate

Status: table_creation_decision_recorded_table_disabled.

## Decision

This gate records that `module_projections` table creation is still deferred until an explicit table contract gate.

No Alembic revision, `module_projections` database table, SQLAlchemy model, projection write service, worker materialization, or new runtime route is opened in this gate.

## Safe bundling policy

Future steps may be bundled only when all bundled changes remain inside one safety boundary and do not open new runtime, database, route, worker, queue, GPU/CUDA, or write-service scope. Accuracy and stability take priority over speed.

## Required table contract preconditions

- Migration implementation decision recorded.
- Tenant foreign-key policy finalized.
- ModuleRun cascade policy finalized.
- ModuleResult cascade policy finalized.
- Unique active projection constraint finalized.
- Projection hash and source hash policy finalized.
- Retention and role visibility policy finalized.
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

`radi144_materialized_projection_table_contract_gate_decision` must exist before an Alembic revision, ORM model, or `module_projections` table is introduced.

## Verification

Run:

```bash
make verify
```
