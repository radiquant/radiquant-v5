# Radi144 Projection Gate Ergonomics

Status: ergonomics_anchor_recorded.

## Purpose

This document reduces operator/developer friction while preserving the current safety boundary.
It is an ergonomics-only artifact and does not open projection storage, migration, ORM, write-service, worker materialization, GPU/CUDA, API-triggered execution, or new runtime routes.

## Current status

- Completed gate: `radi144_materialized_projection_migration_file_repository_file_admission_gate_decision`
- Next phase: `radi144_materialized_projection_migration_file_repository_file_admission_implementation_gate_decision`
- Source of truth: `module_results.result_payload_json`
- Projection read mode: on-demand via existing Radi144 API projection read boundary
- Code features allowed for next phase: false

## Safe future bundling policy

Future steps may be bundled only when they remain within one safety boundary and do not open database schema creation, runtime routes, worker materialization, write-service enablement, GPU/CUDA execution, or external queue/daemon execution. Accuracy and stability remain higher priority than speed.

## Stable gate checklist

For every Radi144 materialized projection gate, verify:

1. Contract/schema exists when the gate is contract-bearing.
2. Instance exists when the gate is contract-bearing.
3. Radi144 manifest links the gate or the gate is explicitly documented as ergonomics-only.
4. `docs/pi/project.yml` records status, decision, document, validator, tests, future gate, invariants, and blockers.
5. Validator exists and fails closed on forbidden implementation tokens.
6. Test exists and runs the validator.
7. `scripts/verify_bootstrap.py` includes the validator/test/document where applicable.
8. `make verify` is green.
9. Blocked scopes remain blocked.

## Opened scopes

- Radi144 CPU-safe execution service
- Radi144 worker CPU execution wiring
- Radi144 runtime result write service
- Radi144 projection builder service
- Radi144 API projection reads
- Radi144 JobTracker event binding

## Still blocked

- Alembic projection migration
- `module_projections` database table
- materialized projection ORM model
- projection write service
- worker projection materialization
- projection cache storage
- raw/debug/internal projection storage
- new projection runtime route
- GPU/CUDA execution
- API-triggered execution
- external queue/daemon execution

## Verification

Run:

```bash
python3 scripts/check_radi144_projection_gate_ergonomics.py
make verify
```
