# Radi144 Result Persistence Storage Gate

Status: storage model initialized; runtime writes blocked.

## Decision

The Radi144 result persistence gate is opened as a **storage-only** gate.

This creates the tenant-scoped storage model and migration for the engine domain MVP entities:

- `ModuleRun`
- `ModuleResult`
- `ModuleProvenance`

runtime writes remain blocked. No service writes module results yet, no result API is opened, no projection builder runs, no worker job is created, and engine execution remains blocked.

## Added storage artifacts

- `apps/api/app/models/engine.py`
- `apps/api/alembic/versions/0007_engine_result_storage.py`
- `packages/contracts/storage/radi144-result-storage.schema.v1.json`
- `packages/contracts/storage/radi144-result-storage.v1.instance.json`
- `scripts/check_radi144_result_persistence_storage.py`
- `tests/test_radi144_result_persistence_storage.py`

## Storage invariants

- All storage tables are tenant-scoped.
- `module_results` requires retention metadata.
- `module_provenances` stores reproducibility metadata.
- Raw/debug/internal columns are forbidden.
- `client_projection_required` stays true.
- Projection status stays `pending_projection_builder`.
- `ModuleInput` and `ModuleOutput` remain deferred.

## Still blocked

- `runtime_result_writes`
- `engine_api_runtime_routes`
- `client_projection_builder`
- `worker_jobs`
- `engine_execution`

## Why storage before runtime writes?

Storage can be verified independently as a contract/model/migration boundary. Runtime writes need API-route authorization, event-truth linkage, and worker lifecycle decisions. Those are intentionally later gates.

## Next gate

The next optimal gate is `radi144_engine_api_runtime_route_gate_decision`.

Reason: result storage, job lifecycle, API boundary, and projection boundary are now contractually fixed. The next decision can safely consider opening tenant-scoped non-executing runtime routes while still keeping engine execution and workers blocked.

## Verification

Run:

```bash
make verify
```

The verification chain checks storage metadata, migrations, contracts, and route drift while confirming that runtime writes, API runtime routes, projection builder, workers, and engine execution remain blocked.
