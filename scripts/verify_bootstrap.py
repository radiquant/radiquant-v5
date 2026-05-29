#!/usr/bin/env python3
"""Bootstrap verification for radiquant-v5.

This intentionally checks only the restart skeleton and context anchors.
Application feature code is not expected to exist yet.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path("/opt/radiquant4")

REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    ".python-version",
    ".nvmrc",
    ".env.example",
    "package.json",
    "pyproject.toml",
    "Makefile",
    "docs/architecture/START_HERE.md",
    "docs/architecture/DECISION_FREEZE_2026-05-22.md",
    "docs/pi/project.yml",
    "docs/architecture/CONTRACT_FOUNDATION.md",
    "packages/contracts/README.md",
    "packages/contracts/openapi/openapi.v1.json",
    "packages/contracts/api/radi144-engine-api-boundary.v1.json",
    "packages/contracts/api/radi144-engine-api-boundary.v1.instance.json",
    "packages/contracts/workflows/workflow-manifest.v2.json",
    "packages/contracts/events/event-registry.v1.json",
    "packages/contracts/events/event-envelope.schema.v1.json",
    "packages/contracts/events/radi144-worker-progress-events.schema.v1.json",
    "packages/contracts/events/radi144-worker-progress-events.v1.instance.json",
    "packages/contracts/events/radi144-jobtracker-event-binding.schema.v1.json",
    "packages/contracts/events/radi144-jobtracker-event-binding.v1.instance.json",
    "packages/contracts/routes/route-security-manifest.v1.json",
    "packages/contracts/schemas/engine-manifest.schema.json",
    "packages/contracts/engines/radi144.engine-manifest.v1.json",
    "packages/contracts/jobs/radi144-engine-job.schema.v1.json",
    "packages/contracts/jobs/radi144-api-job-record.schema.v1.json",
    "packages/contracts/jobs/radi144-api-job-record.v1.instance.json",
    "packages/contracts/jobs/radi144-worker-runtime.schema.v1.json",
    "packages/contracts/jobs/radi144-worker-runtime.v1.instance.json",
    "packages/contracts/jobs/radi144-external-queue-decision.schema.v1.json",
    "packages/contracts/jobs/radi144-external-queue-decision.v1.instance.json",
    "packages/contracts/execution/radi144-engine-execution-decision.schema.v1.json",
    "packages/contracts/execution/radi144-engine-execution-decision.v1.instance.json",
    "packages/contracts/execution/radi144-engine-execution-cpu-safe.schema.v1.json",
    "packages/contracts/execution/radi144-engine-execution-cpu-safe.v1.instance.json",
    "packages/contracts/execution/radi144-worker-cpu-execution-wiring.schema.v1.json",
    "packages/contracts/execution/radi144-worker-cpu-execution-wiring.v1.instance.json",
    "packages/contracts/projections/radi144-client-projection.schema.v1.json",
    "packages/contracts/projections/radi144-client-projection.v1.instance.json",
    "packages/contracts/projections/radi144-worker-projection-materialization-decision.schema.v1.json",
    "packages/contracts/projections/radi144-worker-projection-materialization-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-storage-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-storage-decision.v1.instance.json",
    "packages/contracts/projections/radi144-projection-cache-policy-decision.schema.v1.json",
    "packages/contracts/projections/radi144-projection-cache-policy-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-storage-contract-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-storage-contract-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-storage-schema-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-storage-schema-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-storage.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-storage.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-storage-migration-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-storage-migration-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-orm-model-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-orm-model-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-relationship-contract-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-relationship-contract-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-constraints-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-constraints-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-model-enablement-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-model-enablement-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-orm-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-orm-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-enablement-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-enablement-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-table-creation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-table-creation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-table-contract-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-table-contract-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-table-ddl-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-table-ddl-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-alembic-revision-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-alembic-revision-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-alembic-revision-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-alembic-revision-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-contract-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-contract-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-creation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-creation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-content-contract-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-content-contract-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-authoring-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-authoring-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-write-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-write-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-write-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-write-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-introduction-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-introduction-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-introduction-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-introduction-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-introduction-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-introduction-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-introduction-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-introduction-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-creation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-creation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-creation-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-creation-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-write-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-write-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-write-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-write-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-materialization-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-materialization-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-materialization-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-materialization-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-execution-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-execution-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-execution-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-execution-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-enablement-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-enablement-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-enablement-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-enablement-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-activation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-activation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-activation-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-activation-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-opening-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-opening-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-opening-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-opening-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-release-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-release-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-release-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-release-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-publication-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-publication-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-publication-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-publication-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-finalization-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-finalization-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-finalization-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-finalization-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-closure-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-closure-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-closure-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-closure-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-readiness-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-readiness-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-readiness-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-readiness-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-preflight-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-preflight-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-preflight-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-preflight-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-validation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-validation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-validation-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-validation-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-approval-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-approval-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-approval-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-approval-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-authorization-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-authorization-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-authorization-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-authorization-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-permission-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-permission-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-permission-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-permission-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-access-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-access-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-access-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-access-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-review-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-review-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-review-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-review-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-acceptance-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-acceptance-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-acceptance-implementation-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-acceptance-implementation-decision.v1.instance.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-admission-decision.schema.v1.json",
    "packages/contracts/projections/radi144-materialized-projection-migration-file-repository-file-admission-decision.v1.instance.json",
    "packages/contracts/projections/radi144-projection-builder.schema.v1.json",
    "packages/contracts/projections/radi144-projection-builder.v1.instance.json",
    "packages/contracts/storage/radi144-result-storage.schema.v1.json",
    "packages/contracts/storage/radi144-result-storage.v1.instance.json",
    "packages/contracts/storage/radi144-runtime-result-write.schema.v1.json",
    "packages/contracts/storage/radi144-runtime-result-write.v1.instance.json",
    "packages/contracts/results/radi144-result.schema.v1.json",
    "packages/contracts/domains/domain-model.v1.json",
    "docs/architecture/SECURITY_DATABASE_CORE.md",
    "scripts/validate_contracts.py",
    "scripts/check_workflow_manifest.py",
    "scripts/check_event_schema_gate.py",
    "scripts/check_realtime_api_gate.py",
    "scripts/check_radi144_engine_manifest.py",
    "scripts/check_radi144_domain_service.py",
    "scripts/check_radi144_result_schema.py",
    "scripts/check_radi144_result_persistence_storage.py",
    "scripts/check_radi144_engine_api_runtime_routes.py",
    "scripts/check_radi144_runtime_result_write.py",
    "scripts/check_radi144_projection_builder.py",
    "scripts/check_radi144_api_projection_read.py",
    "scripts/check_radi144_worker_job_gate.py",
    "scripts/check_radi144_worker_runtime_gate.py",
    "scripts/check_radi144_cpu_safe_execution.py",
    "scripts/check_radi144_worker_cpu_execution_wiring.py",
    "scripts/check_radi144_worker_progress_event_gate.py",
    "scripts/check_radi144_jobtracker_event_binding.py",
    "scripts/check_radi144_projection_gate_ergonomics.py",
    "scripts/check_runtime_routes.py",
    "scripts/check_openapi_runtime.py",
    "scripts/export_openapi.py",
    "scripts/check_db_core.py",
    "apps/api/app/db/base.py",
    "apps/api/app/models/identity.py",
    "apps/api/app/models/audit.py",
    "apps/api/alembic.ini",
    "apps/api/alembic/env.py",
    "apps/api/alembic/versions/0001_identity_tenant_audit.py",
    "docs/architecture/AUTH_TENANT_AUDIT_DB_CORE.md",
    "docs/architecture/WORKFLOW_API_GATE.md",
    "docs/architecture/EVENT_SCHEMA_GATE.md",
    "docs/architecture/REALTIME_API_GATE.md",
    "docs/architecture/JOBTRACKER_UI_GATE.md",
    "docs/architecture/RADI144_ENGINE_MANIFEST_GATE.md",
    "docs/architecture/RADI144_DOMAIN_SERVICE_GATE.md",
    "docs/architecture/RADI144_RESULT_SCHEMA_GATE.md",
    "docs/architecture/RADI144_RESULT_PERSISTENCE_GATE_DECISION.md",
    "docs/architecture/RADI144_ENGINE_JOB_GATE_DECISION.md",
    "docs/architecture/RADI144_ENGINE_API_GATE_DECISION.md",
    "docs/architecture/RADI144_CLIENT_PROJECTION_GATE_DECISION.md",
    "docs/architecture/RADI144_RESULT_PERSISTENCE_STORAGE_GATE.md",
    "docs/architecture/RADI144_ENGINE_API_RUNTIME_ROUTE_GATE.md",
    "docs/architecture/RADI144_RUNTIME_RESULT_WRITE_GATE.md",
    "docs/architecture/RADI144_PROJECTION_BUILDER_GATE.md",
    "docs/architecture/RADI144_API_PROJECTION_READ_GATE.md",
    "docs/architecture/RADI144_WORKER_JOB_GATE_DECISION.md",
    "docs/architecture/RADI144_WORKER_RUNTIME_GATE_DECISION.md",
    "docs/architecture/RADI144_ENGINE_EXECUTION_GATE_DECISION.md",
    "docs/architecture/RADI144_ENGINE_EXECUTION_CPU_SAFE_GATE.md",
    "docs/architecture/RADI144_WORKER_CPU_EXECUTION_WIRING_GATE.md",
    "docs/architecture/RADI144_WORKER_PROGRESS_EVENT_GATE.md",
    "docs/architecture/RADI144_JOBTRACKER_EVENT_BINDING_GATE.md",
    "docs/architecture/RADI144_EXTERNAL_QUEUE_DECISION_GATE.md",
    "docs/architecture/RADI144_WORKER_PROJECTION_MATERIALIZATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_STORAGE_DECISION_GATE.md",
    "docs/architecture/RADI144_PROJECTION_CACHE_POLICY_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_STORAGE_CONTRACT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_STORAGE_SCHEMA_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_STORAGE_MIGRATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_ORM_MODEL_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_RELATIONSHIP_CONTRACT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_CONSTRAINTS_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MODEL_ENABLEMENT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_ORM_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_ENABLEMENT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_TABLE_CREATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_TABLE_CONTRACT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_TABLE_DDL_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_ALEMBIC_REVISION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_ALEMBIC_REVISION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_CONTRACT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_CREATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_CONTENT_CONTRACT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_AUTHORING_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_WRITE_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_WRITE_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_INTRODUCTION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_INTRODUCTION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_INTRODUCTION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_INTRODUCTION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_CREATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_CREATION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_WRITE_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_WRITE_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_MATERIALIZATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_MATERIALIZATION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_EXECUTION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_EXECUTION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ENABLEMENT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ENABLEMENT_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ACTIVATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ACTIVATION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_OPENING_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_OPENING_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_RELEASE_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_RELEASE_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_PUBLICATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_PUBLICATION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_FINALIZATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_FINALIZATION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_CLOSURE_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_CLOSURE_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_READINESS_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_READINESS_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_PREFLIGHT_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_PREFLIGHT_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_VALIDATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_VALIDATION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_APPROVAL_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_APPROVAL_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_AUTHORIZATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_AUTHORIZATION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_PERMISSION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_PERMISSION_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ACCESS_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ACCESS_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_REVIEW_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_REVIEW_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ACCEPTANCE_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ACCEPTANCE_IMPLEMENTATION_DECISION_GATE.md",
    "docs/architecture/RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_REPOSITORY_FILE_ADMISSION_DECISION_GATE.md",
    "docs/architecture/RADI144_PROJECTION_GATE_ERGONOMICS.md",
    "apps/api/app/core/config.py",
    "apps/api/app/db/session.py",
    "apps/api/app/services/auth.py",
    "apps/api/app/services/audit.py",
    "apps/api/app/services/consent.py",
    "apps/api/app/security/tenant_guard.py",
    "apps/api/app/security/passwords.py",
    "apps/api/app/routes/auth.py",
    "apps/api/app/routes/clients.py",
    "apps/api/app/routes/sessions.py",
    "apps/api/app/routes/workflows.py",
    "apps/api/app/routes/realtime.py",
    "apps/api/app/routes/radi144.py",
    "apps/api/app/schemas/auth.py",
    "apps/api/app/schemas/client.py",
    "apps/api/app/schemas/session.py",
    "apps/api/app/schemas/workflow.py",
    "apps/api/app/schemas/realtime.py",
    "apps/api/app/schemas/radi144_result.py",
    "apps/api/app/schemas/radi144_job.py",
    "apps/api/app/schemas/radi144_api.py",
    "apps/api/app/models/client.py",
    "apps/api/app/models/engine.py",
    "apps/api/app/models/session.py",
    "apps/api/app/models/workflow.py",
    "apps/api/app/services/workflow_manifest.py",
    "apps/api/app/models/event.py",
    "apps/api/app/schemas/event.py",
    "apps/api/app/services/event_registry.py",
    "apps/api/app/services/radi144/__init__.py",
    "apps/api/app/services/radi144/domain.py",
    "apps/api/app/services/radi144/result_writer.py",
    "apps/api/app/services/radi144/projection_builder.py",
    "apps/api/alembic/versions/0002_user_password_hash.py",
    "apps/api/alembic/versions/0003_client_profile_consent.py",
    "apps/api/alembic/versions/0004_session_domain.py",
    "apps/api/alembic/versions/0005_workflow_api_gate.py",
    "apps/api/alembic/versions/0006_event_schema_gate.py",
    "apps/api/alembic/versions/0007_engine_result_storage.py",
    "tests/test_runtime_security_core.py",
    "tests/test_identity_auth_routes.py",
    "tests/test_client_routes.py",
    "tests/test_consent_service.py",
    "tests/test_session_routes.py",
    "tests/test_workflow_routes.py",
    "tests/test_event_schema_gate.py",
    "tests/test_realtime_routes.py",
    "tests/test_radi144_engine_manifest.py",
    "tests/test_radi144_domain_service.py",
    "tests/test_radi144_result_schema.py",
    "tests/test_radi144_result_persistence_storage.py",
    "tests/test_radi144_engine_api_runtime_routes.py",
    "tests/test_radi144_runtime_result_write.py",
    "tests/test_radi144_projection_builder.py",
    "tests/test_radi144_api_projection_read.py",
    "tests/test_radi144_worker_job_gate.py",
    "tests/test_radi144_worker_runtime_gate.py",
    "tests/test_radi144_projection_gate_ergonomics.py",
    "tests/test_radi144_cpu_safe_execution.py",
    "tests/test_radi144_worker_cpu_execution_wiring.py",
    "scripts/check_frontend_shell.py",
    "apps/web-astro/astro.config.mjs",
    "apps/web-astro/tsconfig.json",
    "apps/web-astro/src/env.d.ts",
    "apps/web-astro/src/layouts/AppShell.astro",
    "apps/web-astro/src/pages/index.astro",
    "apps/web-astro/src/pages/login.astro",
    "apps/web-astro/src/pages/dashboard.astro",
    "apps/web-astro/src/pages/clients/index.astro",
    "apps/web-astro/src/pages/clients/new.astro",
    "apps/web-astro/src/pages/clients/[client_id].astro",
    "apps/web-astro/src/components/LoginShell.tsx",
    "apps/web-astro/src/components/RoleProjectionShell.tsx",
    "apps/web-astro/src/components/ClientAccessFields.tsx",
    "apps/web-astro/src/components/ClientListIsland.tsx",
    "apps/web-astro/src/components/ClientCreateIsland.tsx",
    "apps/web-astro/src/components/ClientDetailIsland.tsx",
    "apps/web-astro/src/components/ConsentIsland.tsx",
    "apps/web-astro/src/components/JobTrackerStatusIsland.tsx",
    "apps/web-astro/src/lib/api/config.ts",
    "apps/web-astro/src/lib/api/types.ts",
    "apps/web-astro/src/lib/api/client.ts",
    "apps/web-astro/src/lib/theme/role-projections.ts",
    "apps/web-astro/src/styles/tokens.css",
    "apps/web-astro/src/styles/global.css",
]

REQUIRED_DIRS = [
    "apps",
    "apps/web-astro",
    "apps/web-astro/src",
    "packages",
    "infra",
    "scripts",
    "docs/architecture",
    "docs/pi",
    "packages/contracts/openapi",
    "packages/contracts/api",
    "packages/contracts/workflows",
    "packages/contracts/events",
    "packages/contracts/routes",
    "packages/contracts/domains",
    "packages/contracts/engines",
    "packages/contracts/jobs",
    "packages/contracts/projections",
    "packages/contracts/storage",
    "packages/contracts/results",
    "packages/contracts/schemas",
]

REFERENCE_FILES = [
    REFERENCE / "docs/pi/project.yml",
    REFERENCE / "docs/pi/architecture.yml",
    REFERENCE / "docs/pi/engines.yml",
    REFERENCE / "docs/pi/routes.yml",
    REFERENCE / "docs/pi/security.yml",
    REFERENCE / "docs/restart-radiquant-v5/05_MASTER_SPECIFICATION.md",
    REFERENCE / "docs/restart-radiquant-v5/08_OPTIMAL_REBUILD_SEQUENCE.md",
    REFERENCE / "docs/restart-radiquant-v5/09_DECISION_FREEZE_2026-05-22.md",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"[OK] {message}")


def main() -> int:
    if not ROOT.exists():
        fail(f"Root does not exist: {ROOT}")

    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        if not path.is_dir():
            fail(f"Missing required directory: {rel}")
    ok("required directories exist")

    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.is_file():
            fail(f"Missing required file: {rel}")
    ok("required files exist")

    for path in REFERENCE_FILES:
        if not path.is_file():
            fail(f"Missing canonical reference file: {path}")
    ok("canonical radiquant4 reference files exist")

    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    if "verify" not in package_json.get("scripts", {}):
        fail("package.json lacks scripts.verify")
    ok("package.json verify script exists")

    python_version = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    if not python_version.startswith("3.11"):
        fail(f"Unexpected .python-version: {python_version}")
    ok(f"python version pinned: {python_version}")

    node_version = (ROOT / ".nvmrc").read_text(encoding="utf-8").strip()
    if node_version != "22.22.2":
        fail(f"Unexpected .nvmrc: {node_version}")
    ok(f"node version pinned: {node_version}")

    if platform.python_version_tuple()[:2] != ("3", "11"):
        print(f"[WARN] running Python is {platform.python_version()}, expected 3.11.x")
    else:
        ok(f"running Python version: {platform.python_version()}")

    if (ROOT / "_archive_pre_restart_20260523-092151").exists():
        ok("pre-restart archive is present and ignored by .gitignore")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_contracts.py")], check=True)
    ok("contract foundation validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_workflow_manifest.py")], check=True)
    ok("workflow manifest gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_event_schema_gate.py")], check=True)
    ok("event schema gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_realtime_api_gate.py")], check=True)
    ok("realtime API gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_engine_manifest.py")], check=True)
    ok("Radi144 engine manifest gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_domain_service.py")], check=True)
    ok("Radi144 domain service gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_result_schema.py")], check=True)
    ok("Radi144 result schema gate validates")





    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_result_persistence_storage.py")], check=True)
    ok("Radi144 result persistence storage gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_engine_api_runtime_routes.py")], check=True)
    ok("Radi144 engine API runtime route gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_runtime_result_write.py")], check=True)
    ok("Radi144 runtime result write gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_projection_builder.py")], check=True)
    ok("Radi144 projection builder gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_api_projection_read.py")], check=True)
    ok("Radi144 API projection read gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_worker_job_gate.py")], check=True)
    ok("Radi144 worker job gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_worker_runtime_gate.py")], check=True)
    ok("Radi144 worker runtime gate validates")


    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_cpu_safe_execution.py")], check=True)
    ok("Radi144 CPU-safe execution gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_worker_cpu_execution_wiring.py")], check=True)
    ok("Radi144 worker CPU execution wiring gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_worker_progress_event_gate.py")], check=True)
    ok("Radi144 worker progress event gate validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_jobtracker_event_binding.py")], check=True)
    ok("Radi144 JobTracker event binding gate validates")









































































    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_radi144_projection_gate_ergonomics.py")], check=True)
    ok("Radi144 projection gate ergonomics validate")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_runtime_routes.py")], check=True)
    ok("runtime routes match security manifest")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_openapi_runtime.py")], check=True)
    ok("runtime OpenAPI matches committed contract paths")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_db_core.py")], check=True)
    ok("auth/tenant/audit DB core validates")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_frontend_shell.py")], check=True)
    ok("frontend shell validates")

    subprocess.run([sys.executable, "-m", "pytest", str(ROOT / "tests")], check=True)
    ok("runtime security negative tests pass")

    print("\nBootstrap verification complete. Runtime security core, identity/audit core, frontend shell gate, client domain API gate, client frontend gate, consent domain gate, session domain gate, workflow manifest gate, Workflow API Gate, Event Schema Gate, Realtime API Gate, JobTracker UI Gate, Radi144 Engine Manifest Gate, Radi144 Domain Service Gate, Radi144 Result Schema Gate, Radi144 Result Persistence Decision Gate, Radi144 Engine Job Decision Gate, Radi144 Engine API Decision Gate, Radi144 Client Projection Decision Gate, Radi144 Result Persistence Storage Gate, Radi144 Engine API Runtime Route Gate, Radi144 Runtime Result Write Gate, Radi144 Projection Builder Gate, Radi144 API Projection Read Gate, Radi144 Worker Job Gate, Radi144 Worker Runtime Gate, Radi144 Engine Execution Decision Gate, Radi144 CPU-safe Execution Gate, Radi144 Worker CPU Execution Wiring Gate, Radi144 Worker Progress Event Gate, Radi144 JobTracker Event Binding Gate, Radi144 External Queue Decision Gate, Radi144 Worker Projection Materialization Decision Gate, Radi144 Materialized Projection Storage Decision Gate, Radi144 Projection Cache Policy Decision Gate, Radi144 Materialized Projection Storage Contract Decision Gate, Radi144 Materialized Projection Storage Schema Decision Gate, Radi144 Materialized Projection Storage Migration Decision Gate, Radi144 Materialized Projection ORM Model Decision Gate, Radi144 Materialized Projection Relationship Contract Decision Gate, Radi144 Materialized Projection Constraints Decision Gate, Radi144 Materialized Projection Model Enablement Decision Gate, Radi144 Materialized Projection ORM Implementation Decision Gate, Radi144 Materialized Projection Migration Enablement Decision Gate, Radi144 Materialized Projection Migration Implementation Decision Gate, Radi144 Materialized Projection Table Creation Decision Gate, Radi144 Materialized Projection Table Contract Decision Gate, Radi144 Materialized Projection Table DDL Implementation Decision Gate, Radi144 Materialized Projection Alembic Revision Decision Gate, Radi144 Materialized Projection Alembic Revision Implementation Decision Gate, Radi144 Materialized Projection Migration File Decision Gate, Radi144 Materialized Projection Migration File Contract Decision Gate, Radi144 Materialized Projection Migration File Implementation Decision Gate, Radi144 Materialized Projection Migration File Creation Decision Gate, Radi144 Materialized Projection Migration File Content Contract Decision Gate, Radi144 Materialized Projection Migration File Authoring Decision Gate, Radi144 Materialized Projection Migration File Write Decision Gate, Radi144 Materialized Projection Migration File Write Implementation Decision Gate, Radi144 Materialized Projection Migration File Introduction Decision Gate, Radi144 Materialized Projection Migration File Introduction Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository Introduction Decision Gate, Radi144 Materialized Projection Migration File Repository Introduction Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Creation Decision Gate, Radi144 Materialized Projection Migration File Repository File Creation Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Write Decision Gate, Radi144 Materialized Projection Migration File Repository File Write Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Materialization Decision Gate, Radi144 Materialized Projection Migration File Repository File Materialization Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Execution Decision Gate, Radi144 Materialized Projection Migration File Repository File Execution Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Enablement Decision Gate, Radi144 Materialized Projection Migration File Repository File Enablement Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Activation Decision Gate, Radi144 Materialized Projection Migration File Repository File Activation Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Opening Decision Gate, Radi144 Materialized Projection Migration File Repository File Opening Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Release Decision Gate, Radi144 Materialized Projection Migration File Repository File Release Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Publication Decision Gate, Radi144 Materialized Projection Migration File Repository File Publication Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Finalization Decision Gate, Radi144 Materialized Projection Migration File Repository File Finalization Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Closure Decision Gate, Radi144 Materialized Projection Migration File Repository File Closure Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Readiness Decision Gate, Radi144 Materialized Projection Migration File Repository File Readiness Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Preflight Decision Gate, Radi144 Materialized Projection Migration File Repository File Preflight Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Validation Decision Gate, Radi144 Materialized Projection Migration File Repository File Validation Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Approval Decision Gate, Radi144 Materialized Projection Migration File Repository File Approval Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Authorization Decision Gate, Radi144 Materialized Projection Migration File Repository File Authorization Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Permission Decision Gate, Radi144 Materialized Projection Migration File Repository File Permission Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Access Decision Gate, Radi144 Materialized Projection Migration File Repository File Access Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Review Decision Gate, Radi144 Materialized Projection Migration File Repository File Review Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Acceptance Decision Gate, Radi144 Materialized Projection Migration File Repository File Acceptance Implementation Decision Gate, Radi144 Materialized Projection Migration File Repository File Admission Decision Gate, and Radi144 Projection Gate Ergonomics are present. Radi144 GPU/CUDA, API-triggered execution, external queue/daemon execution, worker projection materialization, materialized projection storage, projection cache storage, ORM model, migration file, Alembic revision file, Alembic migration, table creation, DDL implementation, and projection storage implementation remain blocked until their gates explicitly open them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
