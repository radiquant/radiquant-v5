# Radi144 Projection Builder Gate

Status: builder service enabled, not wired to API or UI.

## Decision

This gate opens a **service-only** Radi144 projection builder. It creates role-safe client and therapist projections from an already validated `Radi144Result`.

The builder is not wired to API routes, frontend UI, worker jobs, or engine execution.

## Added artifacts

- `apps/api/app/services/radi144/projection_builder.py`
- `packages/contracts/projections/radi144-projection-builder.schema.v1.json`
- `packages/contracts/projections/radi144-projection-builder.v1.instance.json`
- `scripts/check_radi144_projection_builder.py`
- `tests/test_radi144_projection_builder.py`

## Role outputs

- Client: `calm_summary`
- Therapist: `professional_detail`

## Safety invariants

- Client sees no raw/debug/internal data.
- Therapist detail still excludes raw matrices, vectors, debug JSON, tokens, passwords, and internal state.
- Wellbeing-only language is required.
- Medical/healing claims remain forbidden.

## Still blocked

- `api_projection_reads`
- `worker_jobs`
- `engine_execution`

API result routes remain boundary/status routes until a later read gate wires projection reads. Once `radi144_api_projection_read_gate_decision` is present, this gate is superseded by API projection reads while worker jobs remain blocked and engine execution remains blocked.

## Next gate

The next optimal gate is `radi144_api_projection_read_gate_decision`.

Reason: projection builder and result writer are now available internally. The next controlled step can decide whether the result endpoint may read stored results through the projection builder.

## Verification

Run:

```bash
make verify
```
