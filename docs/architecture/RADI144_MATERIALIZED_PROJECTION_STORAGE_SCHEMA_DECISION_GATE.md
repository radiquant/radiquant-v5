# Radi144 Materialized Projection Storage Schema Decision Gate

Status: storage_schema_recorded_implementation_disabled.

## Decision

This gate records the JSON schema for future materialized projection storage while keeping implementation disabled.

No ORM model, Alembic migration, database table, write service, worker materialization, or new runtime route is opened in this gate.

## Opened scope

- `radi144-materialized-projection-storage.schema.v1.json`
- `radi144-materialized-projection-storage.v1.instance.json`
- Decision metadata that the schema exists but implementation is disabled.

## Schema invariants

The schema requires:

- tenant-scoped identifiers
- role-scoped projection payloads
- source result hash
- projection builder version
- retention metadata
- invalidation marker
- `raw_debug_excluded: true`
- implementation flags set to false

## Still blocked

- materialized projection storage table
- projection storage migration
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_storage_migration_gate_decision` must exist before any ORM model, Alembic migration, or database table is introduced.

## Verification

Run:

```bash
make verify
```
