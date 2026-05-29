# Radi144 Worker Job Gate Decision

Status: api_job_records_enabled_without_worker_runtime.

## Decision

This gate opens API-created Radi144 job records only. `POST /engines/radi144/jobs` now creates or returns a tenant-scoped `ModuleRun` with status `queued`.

The gate does **not** start a worker runtime, does **not** write results, and does **not** execute Radi144.

## Opened scope

- API job records backed by `ModuleRun`
- Tenant-scoped create/read of queued Radi144 job records
- Idempotent create behavior by `workflow_step_run_id + module_id`
- Status reads through `GET /engines/radi144/jobs/{job_id}`

## Safety invariants

- Tenant context is required.
- Workflow step must belong to the tenant, workflow run, and session.
- The module must be `radi144` and phase must be `diagnose`.
- The create route does not call the domain service.
- The create route does not call the result writer.
- The create route does not call the projection builder.
- no worker runtime.
- engine execution remains blocked.

## Still blocked

- Worker runtime processor
- Engine execution
- Result production from worker jobs
- GPU/CUDA execution

## Next gate

The next optimal gate is `radi144_worker_runtime_gate_decision`.

That gate may decide whether a worker runtime can safely process queued records. It must still keep engine execution blocked unless an explicit later execution gate opens it.

## Verification

Run:

```bash
make verify
```
