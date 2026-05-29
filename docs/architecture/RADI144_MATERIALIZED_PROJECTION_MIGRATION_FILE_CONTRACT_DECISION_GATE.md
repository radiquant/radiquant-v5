# Radi144 Materialized Projection Migration File Contract Decision Gate

Status: migration_file_contract_recorded_no_file.

## Decision

This gate records the future migration file contract for `apps/api/alembic/versions/0008_module_projections.py` without creating the file.

No migration file, Alembic revision file, `module_projections` database table, SQLAlchemy model, projection write service, worker materialization, or new runtime route is opened in this gate.

## Planned file contract

| Area | Contract |
|---|---|
| Planned file | `apps/api/alembic/versions/0008_module_projections.py` |
| Revision | `0008_module_projections` |
| Down revision | `0007_engine_result_storage` |
| Upgrade operation 1 | create `module_projections` table from table contract columns |
| Upgrade operation 2 | create tenant/run/result foreign keys |
| Upgrade operation 3 | create role/schema/raw-debug check constraints |
| Upgrade operation 4 | create tenant/result/run/source-hash indexes |
| Upgrade operation 5 | create partial unique active projection index |
| Downgrade operation 1 | drop partial unique active projection index |
| Downgrade operation 2 | drop projection indexes |
| Downgrade operation 3 | drop `module_projections` table |

## Dialect notes

- SQLite partial unique index requires a `WHERE invalidated_at IS NULL` clause.
- PostgreSQL partial unique index requires the equivalent dialect-specific `postgresql_where` handling.
- JSON column strategy must follow the existing project JSON strategy.
- Foreign keys must reference tables available after `0007_engine_result_storage`.

## Forbidden in this gate

- creating the migration file
- creating an ORM model
- creating a projection write service
- wiring worker projection materialization
- creating a runtime route
- storing raw/debug/internal payloads

## Required future gate

`radi144_materialized_projection_migration_file_implementation_gate_decision` must exist before `apps/api/alembic/versions/0008_module_projections.py` is introduced.

## Verification

Run:

```bash
make verify
```
