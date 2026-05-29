# Radi144 Materialized Projection Storage Contract Decision Gate

Status: storage_contract_recorded_storage_disabled.

## Decision

This gate records the future materialized projection storage contract without creating storage implementation.

The planned storage entity is `module_projections`, but no ORM model, migration, table, write service, worker materialization, or new runtime route is opened in this gate.

## Opened scope

- Decision contract only.
- Planned storage entity and required contract fields are documented.
- Required forbidden fields are documented.
- API read projections remain on-demand from `module_results.result_payload_json`.

## Planned contract fields

A future storage schema must include at least:

- `tenant_id`
- `module_run_id`
- `module_result_id`
- `role`
- `projection_schema_id`
- `projection_builder_version`
- `source_result_hash`
- `retention_json`
- `projection_payload_json`
- `invalidated_at`

## Forbidden future fields

A future storage schema must not include:

- `raw_debug`
- `debug_json`
- `internal_state`
- `client_vector`
- `raw_resonance_matrix`
- `normalized_matrix`

## Still blocked

- materialized projection storage table
- projection storage migration
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_storage_schema_gate_decision` must exist before any ORM model, Alembic migration, table, or write service is introduced.

## Verification

Run:

```bash
make verify
```
