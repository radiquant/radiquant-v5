#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Migration File Write Decision Gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401,E402
from app.db.base import Base  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-migration-file-write-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-migration-file-write-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_WRITE_DECISION_GATE.md"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"
PLANNED_MIGRATION_FILE = MIGRATIONS / "0008_module_projections.py"

FORBIDDEN_IMPLEMENTATION_TOKENS = {
    "class ModuleProjection",
    "__tablename__ = \"module_projections\"",
    "op.create_table(\"module_projections\"",
    "op.create_table('module_projections'",
    "ProjectionWriteService",
    "persist_projection",
}
REQUIRED_PRECONDITIONS = {
    "migration_file_authoring_decision_recorded",
    "migration_file_content_contract_decision_recorded",
    "planned_revision_file_path_confirmed",
    "planned_revision_identifiers_confirmed",
    "content_contract_confirmed",
    "authoring_preconditions_confirmed",
    "migration_file_still_absent",
    "module_projections_table_still_absent",
    "orm_model_still_blocked",
    "write_service_still_blocked",
    "worker_materialization_still_blocked",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(DECISION_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(DECISION_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("migration_file_write_decision_recorded") is not True:
        fail("Radi144 migration file write decision must be recorded")
    for flag in ["migration_file_enabled", "alembic_revision_file_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_migration_file_write_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-migration-file-write-decision.v1.instance.json":
        fail("Radi144 manifest must link migration file write decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 migration file write decision schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 migration file write decision boundary schema_id drift")
    if instance.get("decision") != "defer_migration_file_write_until_write_implementation_gate":
        fail("Radi144 migration file write must be deferred until write implementation gate")
    if instance.get("planned_revision_file") != "apps/api/alembic/versions/0008_module_projections.py" or boundary.get("planned_revision_file") != "apps/api/alembic/versions/0008_module_projections.py":
        fail("Radi144 planned migration file path drift")
    if instance.get("planned_down_revision") != "0007_engine_result_storage" or boundary.get("planned_down_revision") != "0007_engine_result_storage":
        fail("Radi144 planned down revision must be 0007_engine_result_storage")
    if instance.get("required_future_gate") != "radi144_materialized_projection_migration_file_write_implementation_gate_decision":
        fail("Radi144 migration file write must point to migration file write implementation future gate")
    if instance.get("migration_file_write_allowed") is not False or boundary.get("migration_file_write_allowed") is not False:
        fail("Radi144 migration file write must remain disallowed")
    if instance.get("migration_file_authoring_allowed") is not False or boundary.get("migration_file_authoring_allowed") is not False:
        fail("Radi144 migration file authoring must remain disallowed")
    if instance.get("migration_file_creation_allowed") is not False or boundary.get("migration_file_creation_allowed") is not False:
        fail("Radi144 migration file creation must remain disallowed")
    for flag in ["migration_file_enabled", "alembic_revision_file_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 migration file write {flag} must remain false")

    preconditions = set(instance.get("write_preconditions", []))
    if not REQUIRED_PRECONDITIONS.issubset(preconditions):
        fail(f"Radi144 migration file write missing preconditions: {sorted(REQUIRED_PRECONDITIONS - preconditions)}")

    if "module_projections" in set(Base.metadata.tables):
        fail("module_projections table must remain absent in migration file write decision gate")
    if PLANNED_MIGRATION_FILE.exists():
        fail("0008_module_projections.py must not exist in migration file write decision gate")
    implementation_text = "\n".join([
        ENGINE_MODEL.read_text(encoding="utf-8"),
        WORKER_RUNTIME.read_text(encoding="utf-8"),
        ROUTE_FILE.read_text(encoding="utf-8"),
        "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py")),
    ])
    for token in FORBIDDEN_IMPLEMENTATION_TOKENS:
        if token in implementation_text:
            fail(f"Projection migration file implementation must remain absent: {token}")

    for token in [
        "radi144_materialized_projection_migration_file_write_gate_decision",
        "status: migration_file_write_deferred_no_file",
        "radi144_materialized_projection_migration_file_write_implementation_gate_decision",
        "safe_bundling_only_within_single_safety_boundary",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing migration file write token: {token}")
    for blocker in ["migration_file", "alembic_projection_revision_file", "alembic_projection_migration", "module_projections_database_table", "materialized_projection_orm_model", "projection_write_service", "worker_projection_materialization"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["Planned write target", "write deferred", "radi144_materialized_projection_migration_file_write_implementation_gate_decision"]:
        if token not in decision_text:
            fail(f"Migration file write doc missing token: {token}")

    print("[OK] Radi144 materialized projection migration file write decision is recorded")
    print("[OK] Migration file, revision file, migration, table, ORM model, write service, worker materialization, and route remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
