# Radi144 Client Projection Gate Decision

Status: boundary decided; builder not opened.

## Decision

The Radi144 client projection gate is opened only as a **boundary-only** contract. The projection builder remains closed.

This establishes what may eventually be shown to each role without creating UI, result APIs, persistence, worker jobs, or engine execution.

## Boundary recorded

Contract artifacts:

- `packages/contracts/projections/radi144-client-projection.schema.v1.json`
- `packages/contracts/projections/radi144-client-projection.v1.instance.json`
- `scripts/check_radi144_client_projection_decision.py`
- `tests/test_radi144_client_projection_decision.py`

Role boundaries:

- Client: `calm_summary`
- Therapist: `professional_detail`

The client sees no raw/debug/internal data.
The therapist may eventually see professional detail such as workflow steps, substeps, confidence, provenance, and retention metadata, but still not raw matrices, client vectors, debug JSON, tokens, passwords, or internal state.

## Still blocked

- `client_projection_builder`
- `result_persistence`
- `engine_api_runtime_routes`
- `worker_jobs`
- `engine_execution`

The result schema keeps `client_projection.status = pending_projection_builder` until a later implementation gate opens an actual builder.

## Safety invariants

- Wellbeing-only language is required.
- Medical/healing claims remain forbidden.
- Raw/debug/internal result fields are excluded.
- Tenant scope and purpose requirements remain mandatory.
- No frontend URL may be added without OpenAPI/runtime contract.

## Next gate

The next optimal gate is `radi144_result_persistence_storage_gate_decision`.

Reason: the result schema, job lifecycle boundary, API boundary, and projection boundary are now all decided. Persistence can be reconsidered as a storage contract/model gate while still keeping engine execution and runtime workers blocked.

## Verification

Run:

```bash
make verify
```

The verification chain checks that projection boundaries are recorded while projection builder, persistence, engine API runtime routes, workers, and execution remain blocked.
