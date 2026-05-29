# Radi144 Materialized Projection Alembic Revision Decision Gate

Status: alembic_revision_decision_recorded_no_revision_file.

## Decision

This gate reserves the planned revision identity `0008_module_projections` for the future `module_projections` table migration, but does not create an Alembic revision file.

No Alembic revision file, `module_projections` database table, SQLAlchemy model, projection write service, worker materialization, or new runtime route is opened in this gate.

## Planned revision

| Field | Value |
|---|---|
| Planned revision | `0008_module_projections` |
| Expected dependency | `0007_engine_result_storage` |
| Planned table | `module_projections` |
| Status | reserved only, no revision file |

## Required revision preconditions

- DDL implementation decision recorded.
- Revision identifier reserved.
- Dependency on `0007_engine_result_storage` preserved.
- Upgrade/downgrade test plan defined.
- SQLite partial index strategy finalized.
- PostgreSQL partial index strategy finalized.
- JSON column compatibility finalized.
- ORM model still blocked.
- Projection write service still blocked.

## Still blocked

- Alembic projection revision file
- Alembic projection migration
- `module_projections` database table
- materialized projection ORM model
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_alembic_revision_implementation_gate_decision` must exist before an Alembic revision file or `module_projections` DDL is introduced.

## Verification

Run:

```bash
make verify
```
