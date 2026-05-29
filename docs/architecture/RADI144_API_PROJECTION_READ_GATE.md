# Radi144 API Projection Read Gate

Status: api_projection_reads_enabled.

## Decision

This gate wires the existing Radi144 result endpoint to read stored `ModuleResult` payloads through the role-safe `Radi144ProjectionBuilder`.

Projection reads are enabled for:

- `GET /engines/radi144/jobs/{job_id}/result?role=client`
- `GET /engines/radi144/jobs/{job_id}/result?role=therapist`

The route treats `job_id` as the stored `ModuleRun.id` until a later worker/job runtime table is opened.

## Safety invariants

- Tenant context is required.
- Stored payloads are read only through the projection builder.
- Client projection exposes no raw/debug/internal data.
- Therapist projection excludes raw matrices, vectors, debug JSON, tokens, passwords, and internal state.
- No runtime result writes occur in this route.
- No worker runtime is started.
- No engine execution is triggered.

## Still blocked

- `worker_runtime`
- `engine_execution`

worker jobs remain blocked.
engine execution remains blocked.

## Next gate

The next optimal gate is `radi144_worker_job_gate_decision`.

Reason: route, storage, writer, and projection reads are now contract-safe. A later gate can decide whether to create real job runtime records while still keeping actual engine execution blocked unless separately opened.

## Verification

Run:

```bash
make verify
```
