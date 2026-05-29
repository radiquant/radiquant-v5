# 02 — Phasenplan

## Phase A — Contract- und Runtime-Baseline

**Status:** abgeschlossen.

Erledigt:

- Radi144 Engine Manifest vorhanden und validiert.
- Result Schema, Result Storage und Runtime Result Write Boundary vorhanden.
- Projection Builder und API Projection Reads sind contract-bound und on-demand.
- Worker Runtime, CPU-safe Execution und JobTracker Event Binding sind validiert.

Weiterhin begrenzt:

- Keine materialisierte Projection Storage Runtime.
- Keine Projection Write Materialization.
- Keine neue Projection Runtime Route.

## Phase B — Materialized Projection Decision Foundation

**Status:** abgeschlossen.

Erledigt:

- Storage Decision
- Cache Policy Decision
- Storage Contract Decision
- Storage Schema Decision
- Storage Migration Decision
- ORM Model Decision
- Relationship Contract Decision
- Constraints Decision
- Model Enablement Decision
- ORM Implementation Decision
- Migration Enablement Decision
- Migration Implementation Decision
- Table Creation Decision
- Table Contract Decision
- Table DDL Implementation Decision
- Alembic Revision Decision
- Alembic Revision Implementation Decision

Ergebnis:

- Die Zielrichtung ist dokumentiert.
- Die eigentliche Tabelle, ORM-Implementierung und Migration bleiben blockiert.

## Phase C — Migration File Governance

**Status:** weit fortgeschritten, aber noch nicht abgeschlossen.

Erledigt:

- Migration File Decision
- Migration File Contract Decision
- Migration File Implementation Decision
- Migration File Creation Decision
- Migration File Content Contract Decision
- Migration File Authoring Decision
- Migration File Write Decision
- Migration File Write Implementation Decision
- Migration File Introduction Decision
- Migration File Introduction Implementation Decision
- Repository Introduction Decision
- Repository Introduction Implementation Decision
- Repository File Creation Decision
- Repository File Creation Implementation Decision
- Repository File Write Decision
- Repository File Write Implementation Decision
- Repository File Materialization Decision
- Repository File Materialization Implementation Decision
- Repository File Execution Decision
- Repository File Execution Implementation Decision
- Repository File Enablement Decision
- Repository File Enablement Implementation Decision
- Repository File Activation Decision
- Repository File Activation Implementation Decision
- Repository File Opening Decision
- Repository File Opening Implementation Decision
- Repository File Release Decision
- Repository File Release Implementation Decision
- Repository File Publication Decision
- Repository File Publication Implementation Decision
- Repository File Finalization Decision
- Repository File Finalization Implementation Decision
- Repository File Closure Decision
- Repository File Closure Implementation Decision
- Repository File Readiness Decision
- Repository File Readiness Implementation Decision
- Repository File Preflight Decision
- Repository File Preflight Implementation Decision
- Repository File Validation Decision
- Repository File Validation Implementation Decision
- Repository File Approval Decision
- Repository File Approval Implementation Decision
- Repository File Authorization Decision
- Repository File Authorization Implementation Decision
- Repository File Permission Decision
- Repository File Permission Implementation Decision
- Repository File Access Decision
- Repository File Access Implementation Decision
- Repository File Review Decision
- Repository File Review Implementation Decision

Nächster Schritt:

- Repository File Acceptance Decision

## Phase D — Tatsächliche Alembic-/DB-Artefakte

**Status:** 0% aktiviert, bewusst blockiert.

Offen:

- `apps/api/alembic/versions/0008_module_projections.py`
- Alembic revision id `0008_module_projections`
- down revision `0007_engine_result_storage`
- Tabelle `module_projections`
- DDL-Details und Rollback-Pfad

## Phase E — ORM, Write Service, Worker Materialization

**Status:** 0% aktiviert, bewusst blockiert.

Offen:

- `ModuleProjection` ORM-Modell
- Tenant-/Workflow-/ModuleRun-/Result-Beziehungen
- Projection Write Service
- Worker Projection Materialization
- Backfill-/Idempotenz-/Retry-Policy

## Phase F — Runtime/API/Frontend/Ops

**Status:** teilweise vorbereitet, materialisierte Projection Runtime noch blockiert.

Vorhanden:

- On-demand API Projection Reads aus gespeicherten Result Payloads.
- Route Security Manifest und OpenAPI Checks.

Offen:

- Neue materialisierte Projection Runtime Route, falls später erforderlich.
- OpenAPI-Contract und Route-Security-Manifest für jede neue Route.
- Monitoring, Backfill-Runbook, Retention- und Cleanup-Policy für materialisierte Projektionen.
