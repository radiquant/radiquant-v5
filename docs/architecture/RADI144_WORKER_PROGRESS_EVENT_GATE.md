# Radi144 Worker Progress Event Gate

Status: worker_progress_events_enabled_no_api_trigger_no_external_queue.

## Decision

This gate wires Radi144 internal worker processing to the durable event-truth log through `EventWriter`.

The worker now appends public-safe progress records while processing queued CPU-safe jobs:

- `job.running`
- `module.radi144.started`
- `module.radi144.completed`
- `job.done`
- `module.radi144.failed`
- `job.failed`

## Opened scope

- Worker runtime may append tenant-scoped event records.
- Events include session/workflow/step ids when available.
- Event payloads remain public-safe and registry-validated.

## Still blocked

- `gpu_cuda_execution`
- `api_triggered_execution`
- `external_queue_daemon`
- `jobtracker_event_binding`
- worker projection building

## Safety invariants

- EventWriter validates event types and forbidden payload keys.
- No raw/debug/internal fields are written to event payloads.
- GPU/CUDA remains blocked.
- API-triggered execution remains blocked.
- External queue/daemon execution remains blocked.
- JobTracker UI is not yet bound to these worker events.

## Next gate

The next optimal gate is `radi144_jobtracker_event_binding_gate_decision`.

That gate can bind the existing JobTracker UI/status surface to event-truth records without opening API-triggered execution or external daemon runtime.

## Verification

Run:

```bash
make verify
```
