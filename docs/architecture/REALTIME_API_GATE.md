# Realtime API Gate

Status: initialized with tenant-scoped SSE replay, fallback polling, route contracts, validator, and tests (2026-05-23).

## Scope opened

The Realtime API Gate opens event-log replay only:

- `GET /sessions/{session_id}/events`
  - fallback polling response
  - validated `after_event_id` replay cursor
  - tenant/session filtered server-side
- `GET /sessions/{session_id}/events/stream`
  - finite `text/event-stream` replay batch
  - uses the same validated cursor and tenant/session guard

## Explicitly still blocked

- Workflow UI and progress components
- JobTracker runtime/state machine
- Engine execution
- Module results
- Synthesized/fake progress
- WebSocket/WebTransport bidirectional hardware paths

## Contract invariants

- Realtime routes are classified as `tenant` in `route-security-manifest.v1.json`.
- Runtime OpenAPI paths must match `openapi.v1.json`.
- Tokens in URLs remain forbidden; auth stays in headers via existing tenant guard.
- Fallback polling is available whenever SSE replay is available.
- Replay cursor must reference an event owned by the same tenant and session.
- Event payload safety remains governed by the Event Schema Gate.

## Verification

`make verify` is the gate command. Current Realtime API Gate baseline: 69 tests passed, 17 runtime routes classified, 12 runtime OpenAPI paths matched.
