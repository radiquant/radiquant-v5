# Radi144 Materialized Projection Constraints Decision Gate

Status: constraints_recorded_model_disabled.

## Decision

This gate records the future constraints for `ModuleProjection` while keeping the ORM model disabled.

No SQLAlchemy model, Alembic migration, database table, write service, worker materialization, or new runtime route is opened in this gate.

## Planned constraints

- `tenant_id` not null
- `module_run_id` not null
- `module_result_id` not null
- role limited to `client` and `therapist`
- source result hash not null
- projection schema ID not null
- projection payload JSON not null
- unique active projection per module result and role
- raw/debug columns forbidden

## Forbidden columns

- `raw_debug`
- `debug_json`
- `internal_state`
- `client_vector`
- `raw_resonance_matrix`
- `normalized_matrix`

## Still blocked

- materialized projection ORM model
- Alembic projection migration
- materialized projection storage table
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_model_enablement_gate_decision` must exist before the ORM model is introduced.

## Verification

Run:

```bash
make verify
```
