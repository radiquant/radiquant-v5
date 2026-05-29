# Radi144 Materialized Projection Table Contract Decision Gate

Status: table_contract_recorded_no_table.

## Decision

This gate records the planned `module_projections` table contract without implementing DDL, Alembic revision, SQLAlchemy model, projection write service, worker materialization, or a new runtime route.

## Planned table contract

| Area | Contract |
|---|---|
| Table | `module_projections` |
| Primary key | `id` UUID |
| Tenant isolation | `tenant_id -> tenants.id` with `RESTRICT` |
| Source run | `module_run_id -> module_runs.id` with `CASCADE` |
| Source result | `module_result_id -> module_results.id` with `CASCADE` |
| Role scope | `role IN ('client', 'therapist')` |
| Projection schema | `radi144_client_projection_v1` or `radi144_therapist_projection_v1` |
| Active uniqueness | one active projection per tenant/result/role/schema where `invalidated_at IS NULL` |
| Source integrity | `source_result_hash` required |
| Payload | role-safe `projection_payload_json` only |
| Retention | `retention_json` required |
| Forbidden data | raw/debug/internal/vector/matrix columns forbidden |

## Still blocked

- Alembic projection migration
- `module_projections` database table
- materialized projection ORM model
- projection write service
- worker projection materialization
- raw/debug/internal projection storage
- new projection runtime route

## Required future gate

`radi144_materialized_projection_table_ddl_implementation_gate_decision` must exist before DDL or an Alembic revision is introduced.

## Verification

Run:

```bash
make verify
```
