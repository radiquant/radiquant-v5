# Workflow API Gate

Status: initialized with contracts, routes, models, migration, and tests (2026-05-23).

## Scope opened

The Workflow API Gate opens manifest-derived workflow planning only:

- `POST /sessions/{session_id}/workflow-runs`
- `GET /sessions/{session_id}/workflow-runs`
- `workflow_runs` and `workflow_step_runs` tenant-scoped tables
- plan generation from `packages/contracts/workflows/workflow-manifest.v2.json`
- consent checks from each workflow's `required_consent_purposes`
- audit append with `AuditAction.WORKFLOW_PLAN`

## Explicitly still blocked

- Workflow UI
- Realtime/SSE/WebSocket progress
- Engine execution
- Module results and result projections
- Raw/debug output

## Contract invariants

- Every runtime route is classified in `route-security-manifest.v1.json`.
- Runtime OpenAPI path/operation set must match `openapi.v1.json`.
- Workflow steps are created only from manifest `module_order` entries.
- Configurable, feature-flagged, or later-gate workflows return a safe conflict response.
- Tenant mismatches return not found without revealing cross-tenant existence.

## Verification

`make verify` is the gate command. Current Workflow API Gate baseline: 51 tests passed, 15 runtime routes classified, 10 runtime OpenAPI paths matched.
