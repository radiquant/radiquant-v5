# Radi144 Engine Manifest Gate

Status: initialized as contract-only first-vertical engine manifest (2026-05-23).

## Scope opened

The Radi144 Engine Manifest Gate opens the module contract only:

- `packages/contracts/engines/radi144.engine-manifest.v1.json`
- `packages/contracts/schemas/engine-manifest.schema.json`
- `scripts/check_radi144_engine_manifest.py`
- `tests/test_radi144_engine_manifest.py`

The manifest defines:

- Radi144 as the first vertical module for `W-A` and `W-B`
- diagnose-phase substeps in the same order as `workflow-manifest.v2.json`
- input/output references
- required event types
- result contract `radi144_result_v1`
- matrix shape `12x12`
- client vector dimensions `256`
- provenance requirements
- safety/privacy invariants

## Explicitly still blocked

- Engine API routes
- result persistence implementation
- client projection builder
- engine execution / worker jobs
- synthetic progress or fake module output

## Contract invariants

- Radi144 substeps must match `module_contracts.radi144.substeps` exactly.
- Every referenced event type must exist in `event-registry.v1.json`.
- Result contract must require provenance, retention metadata, and client projection.
- Raw/debug/internal output must never be client-visible.
- Active analysis consent, tenant-scoped inputs, and Wellbeing-only language are required.
- Engine execution flags remain false until a later explicit gate.
- Domain service may be enabled only as pure in-process logic without API/worker/persistence side effects.

## Verification

`make verify` is the gate command. Radi144 Engine Manifest Gate remains a prerequisite for the pure domain service gate.
