# Radi144 Materialized Projection Migration File Content Contract Decision Gate

Status: migration_file_content_contract_recorded_no_file.

## Decision

This gate records the required content contract for the future Alembic migration file without creating the file.

`apps/api/alembic/versions/0008_module_projections.py` remains absent. No migration file, Alembic revision file, `module_projections` database table, SQLAlchemy model, projection write service, worker materialization, or new runtime route is opened in this gate.

## Planned file identity

| Field | Value |
|---|---|
| Planned file | `apps/api/alembic/versions/0008_module_projections.py` |
| Revision | `0008_module_projections` |
| Down revision | `0007_engine_result_storage` |
| Branch labels | `None` |
| Depends on | `None` |
| Planned table | `module_projections` |
| Status | content contract recorded, no file created |

## Required content sections

- module docstring with gate name and deferred status
- revision identifiers
- `upgrade()` function
- `downgrade()` function
- dialect-specific partial-index notes

## Required imports

- `from alembic import op`
- `import sqlalchemy as sa`

## Required upgrade content

- create `module_projections` table
- create tenant/run/result foreign keys
- create role/schema/raw-debug check constraints
- create tenant/result/run/source-hash indexes
- create partial unique active projection index

## Required downgrade content

- drop partial unique active projection index
- drop projection indexes
- drop `module_projections` table

## Forbidden content

- data backfill
- mutation of `module_results.result_payload_json`
- ORM model definition
- projection write service
- worker materialization
- runtime route
- raw/debug/internal payload storage

## Required future gate

`radi144_materialized_projection_migration_file_authoring_gate_decision` must exist before `apps/api/alembic/versions/0008_module_projections.py` is introduced.

## Verification

Run:

```bash
make verify
```
