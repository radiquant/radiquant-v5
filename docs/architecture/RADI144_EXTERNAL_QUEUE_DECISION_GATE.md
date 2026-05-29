# Radi144 External Queue Decision Gate

Status: external_queue_deferred_internal_worker_only.

## Decision

This gate records a conservative no-go for an external queue/daemon in the current Radi144 vertical slice.

Radi144 already has an internal CPU-safe worker service that can process one queued `ModuleRun` inside a caller-owned transaction. That is enough for the current controlled rebuild gate. A durable operations worker may be opened later only through `radi144_operations_worker_gate_decision`.

## Opened scope

- Decision contract only.
- Manifest records that an external queue decision exists.
- Existing internal worker service remains the only allowed worker invocation boundary.

## Still blocked

- external queue/daemon execution
- public worker control API
- API-triggered execution
- GPU/CUDA execution
- unbounded worker loops
- queue libraries such as Celery/RQ/Arq/Dramatiq

## Safety invariants

- No new runtime route.
- No external daemon process.
- No API-triggered execution.
- No GPU/CUDA path.
- Caller remains transaction owner.
- Progress remains event-truth based.

## Required future gate

`radi144_operations_worker_gate_decision` must exist before any durable queue, daemon, scheduler, or worker process is introduced.

That future gate must define:

- process ownership
- idempotency and locking
- retry/backoff policy
- transaction and shutdown policy
- observability and operator controls
- tenant and consent re-check boundaries

## Verification

Run:

```bash
make verify
```
