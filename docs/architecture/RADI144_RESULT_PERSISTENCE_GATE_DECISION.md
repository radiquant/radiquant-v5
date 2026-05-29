# Radi144 Result Persistence Gate Decision

Status: deferred until upstream engine gates.

## Decision

The Radi144 Result Persistence Gate is **not opened yet**. The current optimal step is a guard decision, not a storage implementation.

Reason: `ModuleRun`, `ModuleResult`, and `ModuleProvenance` must be reproducible and event-truth aligned. Opening storage before the engine job lifecycle, API boundary, and client projection boundary would create orphaned or misleading persisted records.

## Required prerequisites before persistence can open

- `radi144_result_schema_gate` is present and verified.
- `radi144_engine_job_gate` defines the async lifecycle, timeout/fallback semantics, and job status event contract.
- `radi144_engine_api_gate` defines the authenticated tenant-scoped route boundary and OpenAPI contract.
- `radi144_client_projection_gate` defines what can be shown to the client and excludes raw/debug/internal data.

## Current enforced state

The following remain blocked:

- `result_persistence`
- `client_projection_builder`
- `engine_api`
- `worker_jobs`
- `engine_execution`

No `module_runs`, `module_results`, `module_inputs`, `module_outputs`, or `module_provenances` tables are introduced by this decision gate.

## Acceptance criteria

- Radi144 manifest keeps `result_persistence_enabled: false`.
- Radi144 result schema keeps required `retention` and `client_projection` sections.
- No engine storage ORM model or Alembic migration exists yet.
- No engine/result/radi144 API route exists yet.
- `docs/pi/project.yml` records the deferral and advances the next decision to `radi144_engine_job_gate_decision`.

## Verification

Run:

```bash
make verify
```

The verification chain includes `scripts/check_radi144_result_persistence_decision.py` and `tests/test_radi144_result_persistence_decision.py`.
