# Radi144 Runtime Result Write Gate

Status: write service enabled, not wired to API or workers.

## Decision

This gate opens a **service-only** Radi144 result writer. It can persist an already validated `Radi144Result` into `ModuleRun`, `ModuleResult`, and `ModuleProvenance` storage inside an existing transaction.

The service is not wired to API routes, worker jobs, projection builders, or engine execution.

## Added artifacts

- `apps/api/app/services/radi144/result_writer.py`
- `packages/contracts/storage/radi144-runtime-result-write.schema.v1.json`
- `packages/contracts/storage/radi144-runtime-result-write.v1.instance.json`
- `scripts/check_radi144_runtime_result_write.py`
- `tests/test_radi144_runtime_result_write.py`

## Required invariants

- Tenant-scoped `WorkflowStepRun` must exist and match the result tenant/workflow.
- `raw_debug`, `debug_json`, and `internal_state` are rejected.
- `raw_debug_allowed` remains false.
- `client_projection_required` remains true.
- Projection status remains `pending_projection_builder`.
- Provenance metadata is persisted.
- The service flushes but does not commit; callers own transaction boundaries.

## Still blocked

- `api_result_writes`
- `client_projection_builder`
- `worker_jobs`
- `engine_execution`

Runtime API routes remain non-executing and do not call the writer yet.
worker jobs remain blocked.
engine execution remains blocked.

## Next gate

The next optimal gate is `radi144_projection_builder_gate_decision`.

Reason: storage and write service are now available, but any client/therapist-facing result read must pass through the projection boundary first.

## Verification

Run:

```bash
make verify
```
