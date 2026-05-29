# Radi144 Engine Job Gate Decision

Status: initialized as contract-only job lifecycle.

## Decision

The Radi144 Engine Job Gate is opened only at the contract boundary. No worker queue, runtime job processor, engine API, result persistence, client projection builder, GPU path, or engine execution is opened by this gate.

This preserves the current rebuild invariants:

- contract-first
- security-by-default
- tenant-first
- consent-aware
- event-truth
- Wellbeing-only language

## Added contract boundary

- `packages/contracts/jobs/radi144-engine-job.schema.v1.json`
- `apps/api/app/schemas/radi144_job.py`
- `scripts/check_radi144_engine_job_decision.py`
- `tests/test_radi144_engine_job_decision.py`

The job contract records:

- tenant/session/workflow/step identity
- module id `radi144`
- Diagnose phase
- allowed job/module/substep event types
- timeout policy derived from Radi144 manifest substep timeouts
- fail-closed fallback policy
- explicit disabled flags for worker runtime and engine execution

## Still blocked

The following scopes remain closed:

- `worker_jobs`
- `engine_execution`
- `engine_api`
- `result_persistence`
- `client_projection_builder`

## Why no runtime job yet?

A runtime worker would be premature without the route/API gate and without final API security classification. The current gate gives the system a stable event and timeout contract while preventing hidden execution or orphaned results.

## Next gate

The next optimal gate is `radi144_engine_api_gate_decision`.

That gate may decide the authenticated tenant-scoped route boundary and OpenAPI contract. It must still avoid engine execution unless a later runtime/worker gate explicitly opens it.

## Verification

Run:

```bash
make verify
```

The verification chain checks that the job contract aligns with the Radi144 manifest and event registry, and that routes, workers, persistence, projections, and execution remain blocked.
