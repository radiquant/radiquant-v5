# Radi144 Engine API Gate Decision

Status: decision-only boundary not opened.

## Decision

The Radi144 Engine API Gate records the future API boundary but does **not** open runtime API routes yet.

This is intentional: the current project state has a stable job contract, but engine execution, worker jobs, result persistence, and client projection are still blocked. Adding OpenAPI/runtime paths now would imply a callable module surface before the downstream safety and projection boundaries are complete.

## Boundary recorded

Contract artifacts:

- `packages/contracts/api/radi144-engine-api-boundary.v1.json`
- `packages/contracts/api/radi144-engine-api-boundary.v1.instance.json`
- `scripts/check_radi144_engine_api_decision.py`
- `tests/test_radi144_engine_api_decision.py`

Planned future endpoints:

- `POST /engines/radi144/jobs`
- `GET /engines/radi144/jobs/{job_id}`
- `GET /engines/radi144/jobs/{job_id}/result`

These endpoints are tenant-classified, authenticated, tenant-guarded, and non-executing by contract. They are not present in the committed OpenAPI document, route security manifest, or FastAPI runtime yet.

## Still blocked

- `engine_api`
- `worker_jobs`
- `engine_execution`
- `result_persistence`
- `client_projection_builder`

OpenAPI paths remain closed.
runtime FastAPI routes remain closed.
Frontend URLs remain forbidden until an OpenAPI contract and runtime route are opened together in a later gate.

## Safety invariants

- No unclassified route may be added.
- No frontend route may call a missing backend route.
- Tokens in URLs remain forbidden.
- Wellbeing-only language remains required.
- Medical/healing claims remain forbidden.

## Next gate

The next optimal gate is `radi144_client_projection_gate_decision`.

Reason: before opening a result endpoint, the system must decide the client/therapist projection boundary and confirm that raw/debug/internal result fields remain excluded.

## Verification

Run:

```bash
make verify
```

The verification chain checks that the boundary is recorded while OpenAPI paths, route-manifest entries, runtime routes, worker jobs, persistence, projections, and execution remain blocked.
