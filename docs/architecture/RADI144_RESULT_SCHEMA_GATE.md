# Radi144 Result Schema Gate

Status: initialized as contract-only gate.

## Scope

This gate defines the Radi144 result contract before any persistence, projection builder, API route, worker job, GPU path, or engine execution is opened.

Added artifacts:

- `packages/contracts/results/radi144-result.schema.v1.json`
- `apps/api/app/schemas/radi144_result.py`
- `scripts/check_radi144_result_schema.py`
- `tests/test_radi144_result_schema.py`

## Contract invariants

The result schema is identified as `radi144_result_v1` and is linked from `packages/contracts/engines/radi144.engine-manifest.v1.json`.

Required sections:

- tenant/session/workflow/module identifiers
- algorithm and manifest versions
- compute backend marker
- 12x12 matrix shape metadata
- coherence scores and projection-safe biofield map
- confidence metadata in Wellbeing-only language scope
- synergy seed without raw matrix data
- provenance metadata
- retention metadata
- client projection placeholder

## Safety invariants

- Raw debug fields are forbidden.
- Internal state/debug blobs are forbidden.
- Retention metadata is required before persistence can be considered.
- Client projection is required, but the builder remains closed.
- Medical/healing claims remain forbidden; schema language is Wellbeing-only.

## Still blocked

The following scopes remain explicitly closed:

- Result persistence
- Client projection builder
- Radi144 Engine API
- Worker jobs
- GPU/engine execution

## Verification

Run:

```bash
make verify
```

The verification chain includes contract validation, the Radi144 result schema validator, runtime route checks, OpenAPI drift checks, and pytest coverage.
