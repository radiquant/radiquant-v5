# JobTracker UI Gate

Status: initialized with fallback-first React island, central API wrapper binding, static validator, and tests through `make verify` (2026-05-23).

## Scope opened

The JobTracker UI Gate opens a dashboard status display only:

- `apps/web-astro/src/components/JobTrackerStatusIsland.tsx`
- dashboard inclusion in `apps/web-astro/src/pages/dashboard.astro`
- central API wrapper binding for `GET /sessions/{session_id}/events`
- connection states: `connected`, `reconnecting`, `fallback`, `offline`, `failed`, `auth_error`
- fallback replay loading through authenticated headers and tenant context

## Explicitly still blocked

- Engine execution
- Module results
- synthesized/fake progress
- workflow step controls
- WebSocket/WebTransport hardware control
- Job runtime state machine beyond safe connection-state display

## Contract invariants

- Frontend calls remain centralized in `apps/web-astro/src/lib/api/client.ts`.
- The JobTracker UI uses fallback replay; it does not open `EventSource` because header auth is required and tokens in URLs are forbidden.
- The UI displays connection states and safe event metadata only.
- No raw/internal/debug field labels may appear in frontend code.
- `make verify` remains the gate command.

## Verification

Current JobTracker UI Gate baseline: 69 tests passed, 17 runtime routes classified, 12 runtime OpenAPI paths matched, 24 frontend files statically validated.
