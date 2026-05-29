# packages/contracts

Contract foundation for radiquant-v5.

This package is intentionally created before application feature code. It prevents URL, workflow, event and route-security drift.

## Contracts

| Path | Purpose |
|---|---|
| `openapi/openapi.v1.json` | Runtime API contract placeholder; must later be exported from FastAPI and diffed. |
| `workflows/workflow-manifest.v2.json` | Workflow taxonomy, phases, module order and Radi144 first vertical slice. |
| `events/event-registry.v1.json` | Versioned event families, runtime scope flags and payload safety rules. |
| `events/event-envelope.schema.v1.json` | Event Schema Gate envelope contract for durable event truth before realtime. |
| `events/radi144-worker-progress-events.v1*.json` | Radi144 worker event-truth boundary for CPU-safe processing progress. |
| `events/radi144-jobtracker-event-binding.v1*.json` | JobTracker UI binding to Radi144 event truth without execution triggers. |
| `routes/route-security-manifest.v1.json` | Route classification manifest; every API route must be classified. |
| `api/radi144-engine-api-boundary.v1*.json` | Radi144 API boundary; runtime routes are OpenAPI-classified but non-executing. |
| `engines/radi144.engine-manifest.v1.json` | Radi144 first-vertical module contract: inputs, outputs, substeps, events, result and safety invariants. |
| `jobs/radi144-engine-job.schema.v1.json` | Radi144 contract-only engine job lifecycle boundary with event, timeout, and fail-closed invariants. |
| `jobs/radi144-api-job-record.v1*.json` | Radi144 API job record boundary: queued ModuleRun records without worker runtime or execution. |
| `jobs/radi144-worker-runtime.v1*.json` | Radi144 fail-closed worker runtime boundary; no result writes or engine execution. |
| `jobs/radi144-external-queue-decision.v1*.json` | Conservative external queue decision; daemon/queue/public worker API remain blocked. |
| `execution/radi144-engine-execution-decision.v1*.json` | Conservative Radi144 execution decision; CPU/GPU execution deferred to a future gate. |
| `execution/radi144-engine-execution-cpu-safe.v1*.json` | Deterministic CPU-safe Radi144 execution service boundary; not wired to worker/result writes. |
| `execution/radi144-worker-cpu-execution-wiring.v1*.json` | Worker wiring boundary for CPU-safe execution plus result writer; GPU/API-triggered execution blocked. |
| `projections/radi144-client-projection.v1*.json` | Radi144 role projection boundary; client/therapist views exclude raw/debug/internal data. |
| `projections/radi144-worker-projection-materialization-decision.v1*.json` | Conservative worker projection materialization decision; materialized writes/storage remain blocked. |
| `projections/radi144-materialized-projection-storage-decision.v1*.json` | Conservative materialized projection storage decision; projection tables/write services remain blocked. |
| `projections/radi144-projection-cache-policy-decision.v1*.json` | Projection cache policy decision; cache storage/write services remain blocked. |
| `projections/radi144-materialized-projection-storage-contract-decision.v1*.json` | Materialized projection storage contract decision; storage implementation remains blocked. |
| `projections/radi144-materialized-projection-storage-schema-decision.v1*.json` | Materialized projection storage schema decision; schema recorded while ORM/migration/write service remain blocked. |
| `projections/radi144-materialized-projection-storage.v1*.json` | Schema-only future materialized projection storage record contract. |
| `projections/radi144-materialized-projection-storage-migration-decision.v1*.json` | Materialized projection migration decision; Alembic/ORM/table remain blocked. |
| `projections/radi144-materialized-projection-orm-model-decision.v1*.json` | Materialized projection ORM model decision; model implementation remains blocked. |
| `projections/radi144-materialized-projection-relationship-contract-decision.v1*.json` | Materialized projection relationship contract decision; model/table remain blocked. |
| `projections/radi144-materialized-projection-constraints-decision.v1*.json` | Materialized projection constraints decision; ORM/migration/table remain blocked. |
| `projections/radi144-materialized-projection-model-enablement-decision.v1*.json` | Model enablement decision; implementation remains deferred. |
| `projections/radi144-materialized-projection-orm-implementation-decision.v1*.json` | ORM implementation decision; model/migration/table remain deferred. |
| `projections/radi144-materialized-projection-migration-enablement-decision.v1*.json` | Migration enablement decision; Alembic/table/model remain deferred. |
| `projections/radi144-materialized-projection-migration-implementation-decision.v1*.json` | Migration implementation decision; revision/table/model remain deferred. |
| `projections/radi144-materialized-projection-table-creation-decision.v1*.json` | Table creation decision; `module_projections` remains deferred. |
| `projections/radi144-materialized-projection-table-contract-decision.v1*.json` | Table contract decision; DDL/ORM/migration remain deferred. |
| `projections/radi144-materialized-projection-table-ddl-implementation-decision.v1*.json` | DDL implementation decision; Alembic/table remain deferred. |
| `projections/radi144-materialized-projection-alembic-revision-decision.v1*.json` | Alembic revision decision; revision file/table remain deferred. |
| `projections/radi144-materialized-projection-alembic-revision-implementation-decision.v1*.json` | Alembic revision implementation decision; migration file remains deferred. |
| `projections/radi144-materialized-projection-migration-file-decision.v1*.json` | Migration file decision; `0008_module_projections.py` remains deferred. |
| `projections/radi144-materialized-projection-migration-file-contract-decision.v1*.json` | Migration file contract decision; file creation remains deferred. |
| `projections/radi144-materialized-projection-migration-file-implementation-decision.v1*.json` | Migration file implementation decision; `0008_module_projections.py` remains absent. |
| `projections/radi144-materialized-projection-migration-file-creation-decision.v1*.json` | Migration file creation decision; file creation remains deferred. |
| `projections/radi144-materialized-projection-migration-file-content-contract-decision.v1*.json` | Migration file content contract decision; exact future file content is recorded while file creation remains deferred. |
| `projections/radi144-materialized-projection-migration-file-authoring-decision.v1*.json` | Migration file authoring decision; authoring remains deferred until a write gate. |
| `projections/radi144-materialized-projection-migration-file-write-decision.v1*.json` | Migration file write decision; file write remains deferred until an implementation gate. |
| `projections/radi144-materialized-projection-migration-file-write-implementation-decision.v1*.json` | Migration file write implementation decision; file introduction remains deferred. |
| `projections/radi144-materialized-projection-migration-file-introduction-decision.v1*.json` | Migration file introduction decision; repository introduction remains deferred. |
| `projections/radi144-materialized-projection-migration-file-introduction-implementation-decision.v1*.json` | Migration file introduction implementation decision; repository file creation remains deferred. |
| `projections/radi144-materialized-projection-migration-file-repository-introduction-decision.v1*.json` | Migration file repository introduction decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-introduction-implementation-decision.v1*.json` | Migration file repository introduction implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-creation-decision.v1*.json` | Migration file repository file creation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-creation-implementation-decision.v1*.json` | Migration file repository file creation implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-write-decision.v1*.json` | Migration file repository file write decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-write-implementation-decision.v1*.json` | Migration file repository file write implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-materialization-decision.v1*.json` | Migration file repository file materialization decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-materialization-implementation-decision.v1*.json` | Migration file repository file materialization implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-execution-decision.v1*.json` | Migration file repository file execution decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-execution-implementation-decision.v1*.json` | Migration file repository file execution implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-enablement-decision.v1*.json` | Migration file repository file enablement decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-enablement-implementation-decision.v1*.json` | Migration file repository file enablement implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-activation-decision.v1*.json` | Migration file repository file activation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-activation-implementation-decision.v1*.json` | Migration file repository file activation implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-opening-decision.v1*.json` | Migration file repository file opening decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-opening-implementation-decision.v1*.json` | Migration file repository file opening implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-release-decision.v1*.json` | Migration file repository file release decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-release-implementation-decision.v1*.json` | Migration file repository file release implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-publication-decision.v1*.json` | Migration file repository file publication decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-publication-implementation-decision.v1*.json` | Migration file repository file publication implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-finalization-decision.v1*.json` | Migration file repository file finalization decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-finalization-implementation-decision.v1*.json` | Migration file repository file finalization implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-closure-decision.v1*.json` | Migration file repository file closure decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-closure-implementation-decision.v1*.json` | Migration file repository file closure implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-readiness-decision.v1*.json` | Migration file repository file readiness decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-readiness-implementation-decision.v1*.json` | Migration file repository file readiness implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-preflight-decision.v1*.json` | Migration file repository file preflight decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-preflight-implementation-decision.v1*.json` | Migration file repository file preflight implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-validation-decision.v1*.json` | Migration file repository file validation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-validation-implementation-decision.v1*.json` | Migration file repository file validation implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-approval-decision.v1*.json` | Migration file repository file approval decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-approval-implementation-decision.v1*.json` | Migration file repository file approval implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-authorization-decision.v1*.json` | Migration file repository file authorization decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-authorization-implementation-decision.v1*.json` | Migration file repository file authorization implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-permission-decision.v1*.json` | Migration file repository file permission decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-permission-implementation-decision.v1*.json` | Migration file repository file permission implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-access-decision.v1*.json` | Migration file repository file access decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-access-implementation-decision.v1*.json` | Migration file repository file access implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-review-decision.v1*.json` | Migration file repository file review decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-review-implementation-decision.v1*.json` | Migration file repository file review implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-acceptance-decision.v1*.json` | Migration file repository file acceptance decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-acceptance-implementation-decision.v1*.json` | Migration file repository file acceptance implementation decision; migration file remains absent. |
| `projections/radi144-materialized-projection-migration-file-repository-file-admission-decision.v1*.json` | Migration file repository file admission decision; migration file remains absent. |
| `projections/radi144-projection-builder.v1*.json` | Radi144 service-only projection builder boundary; not wired to API/UI/workers/execution. |
| `results/radi144-result.schema.v1.json` | Radi144 result DTO contract with provenance, retention, and projection-placeholder invariants. |
| `storage/radi144-result-storage.v1*.json` | Radi144 storage-only ModuleRun/ModuleResult/ModuleProvenance boundary. |
| `storage/radi144-runtime-result-write.v1*.json` | Radi144 service-only result writer boundary; not wired to API/workers/execution. |
| `schemas/*.schema.json` | JSON Schemas documenting expected contract shape. |

## Rules

- No frontend URL may exist outside OpenAPI/generated client contracts.
- No workflow UI step may exist outside Workflow Manifest v2.
- No API route may exist outside the Route Security Manifest.
- No realtime UI may exist without typed event + fallback state.
