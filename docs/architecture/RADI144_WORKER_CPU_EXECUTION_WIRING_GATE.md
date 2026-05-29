# Radi144 Worker CPU Execution Wiring Gate

Status: worker_cpu_execution_and_result_write_enabled_no_gpu_no_api_trigger.

## Decision

This gate wires the internal Radi144 worker runtime to the CPU-safe execution service and the existing result writer.

The worker can now process queued `ModuleRun` records by:

1. loading tenant-joined workflow/session/client/goal context,
2. asserting active analysis consent,
3. building a deterministic CPU-only `Radi144Result`,
4. persisting it through `Radi144ResultWriter`, and
5. leaving projection building to the existing read-time projection service.

## Opened scope

- Worker runtime may call `Radi144CpuSafeExecutionService`.
- Worker runtime may write validated results through `Radi144ResultWriter`.
- Stored results use `compute_backend = cpu`.

## Still blocked

- `gpu_cuda_execution`
- `api_triggered_execution`
- external queue/daemon execution
- worker projection building
- client projection materialization writes

## Safety invariants

- Active analysis consent is required before CPU execution.
- Tenant joins are required from ModuleRun to WorkflowRun, ClientSession, SessionGoal, and ClientProfile.
- Result writer keeps transaction commit ownership outside the writer.
- Worker runtime does not call GPU/CUDA paths.
- Worker runtime does not build projections.
- Raw/debug/internal fields remain forbidden in persisted result payloads.

## Next gate

The next optimal gate is `radi144_worker_progress_event_gate_decision`.

That gate can decide whether worker processing emits event-truth progress records. API-triggered execution and external queue/daemon execution remain separate gates.

## Verification

Run:

```bash
make verify
```
