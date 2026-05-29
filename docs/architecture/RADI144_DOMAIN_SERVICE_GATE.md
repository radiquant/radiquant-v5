# Radi144 Domain Service Gate

Status: initialized with pure in-process core logic and unit tests (2026-05-23).

## Scope opened

The Radi144 Domain Service Gate opens pure, side-effect-free core functions only:

- `apps/api/app/services/radi144/domain.py`
- `apps/api/app/services/radi144/__init__.py`
- `scripts/check_radi144_domain_service.py`
- `tests/test_radi144_domain_service.py`

Implemented capabilities:

- deterministic 256-dimensional client context vectorization
- default 12-reference-vector catalog
- client-weighted cosine resonance matrix construction
- symmetric 12x12 matrix normalization
- coherence score extraction
- projection-safe biofield map creation
- confidence/uncertainty metadata
- compact synergy seed without raw matrix data

## Explicitly still blocked

- Engine API routes
- worker/job execution
- GPU/CUDA execution path
- result persistence
- client projection builder
- module result UI
- synthetic progress

## Safety and privacy invariants

- Active `analysis` consent is required at domain-input level.
- No DB, FastAPI, worker, event writer, or persistence dependency is imported by the domain service.
- Synergy seed does not expose the raw matrix.
- Output labels stay in Wellbeing language and avoid medical claims.
- Runtime route checks still reject engine/module/result routes until later gates.

## Verification

`make verify` is the gate command. Current Radi144 Domain Service Gate baseline: 80 tests passed, 17 runtime routes classified, 12 runtime OpenAPI paths matched.
