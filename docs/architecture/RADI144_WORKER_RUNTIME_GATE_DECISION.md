# Radi144 Worker Runtime Gate Decision

Status: worker_runtime_service_enabled_fail_closed_no_engine_execution.

## Decision

This gate opens a minimal internal Radi144 worker runtime service that can claim queued `ModuleRun` records and fail closed while the engine execution gate remains closed.

The runtime is deliberately fail-closed: it changes a queued job to `failed_closed` with the public-safe reason `engine_execution_gate_closed`.

## Opened scope

- `apps/api/app/services/radi144/worker_runtime.py`
- `Radi144WorkerRuntimeService.process_next_queued(...)`
- Contract boundary `radi144_worker_runtime_v1`

## Safety invariants

- fail-closed behavior only.
- engine execution remains blocked.
- The worker runtime does not call `Radi144DomainService`.
- The worker runtime does not write results.
- The worker runtime does not call `Radi144ResultWriter`.
- The worker runtime does not build projections.
- The worker runtime does not call GPU/CUDA paths.
- The worker runtime does not own transaction commits.

## Still blocked

- `engine_execution`
- `result_writer_in_worker`
- `projection_builder_in_worker`
- external queue/daemon runtime
- GPU/CUDA execution

## Next gate

The next optimal gate is `radi144_engine_execution_gate_decision`.

That gate must explicitly decide whether actual Radi144 computation may run. Until then, the worker runtime remains fail-closed and produces no result payloads.

## Verification

Run:

```bash
make verify
```
