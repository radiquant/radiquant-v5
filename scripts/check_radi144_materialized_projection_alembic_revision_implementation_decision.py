#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Alembic Revision Implementation Decision Gate."""

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
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-alembic-revision-implementation-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-alembic-revision-implementation-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_ALEMBIC_REVISION_IMPLEMENTATION_DECISION_GATE.md"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"
PLANNED_REVISION_FILE = MIGRATIONS / "0008_module_projections.py"

FORBIDDEN_IMPLEMENTATION_TOKENS = {
    "class ModuleProjection",
    "__tablename__ = \"module_projections\"",
    "op.create_table(\"module_projections\"",
    "op.create_table('module_projections'",
    "ProjectionWriteService",
    "persist_projection",
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
    if runtime_scope.get("alembic_revision_implementation_decision_recorded") is not True:
        fail("Radi144 Alembic revision implementation decision must be recorded")
    for flag in ["alembic_revision_file_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_alembic_revision_implementation_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-alembic-revision-implementation-decision.v1.instance.json":
        fail("Radi144 manifest must link Alembic revision implementation decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 Alembic revision implementation decision schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 Alembic revision implementation decision boundary schema_id drift")
    if instance.get("decision") != "defer_revision_file_until_migration_file_gate":
        fail("Radi144 Alembic revision implementation must defer file creation")
    if instance.get("planned_revision_file") != "apps/api/alembic/versions/0008_module_projections.py" or boundary.get("planned_revision_file") != "apps/api/alembic/versions/0008_module_projections.py":
        fail("Radi144 planned revision file path drift")
    if instance.get("planned_revision") != "0008_module_projections" or boundary.get("planned_revision") != "0008_module_projections":
        fail("Radi144 planned revision must be 0008_module_projections")
    if instance.get("required_future_gate") != "radi144_materialized_projection_migration_file_gate_decision":
        fail("Radi144 Alembic revision implementation must point to migration file future gate")
    for flag in ["alembic_revision_file_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 Alembic revision implementation {flag} must remain false")

    preconditions = set(instance.get("implementation_preconditions", []))
    for precondition in ["alembic_revision_decision_recorded", "planned_revision_file_path_confirmed", "revision_down_revision_confirmed_as_0007_engine_result_storage", "upgrade_function_contract_reviewed", "downgrade_function_contract_reviewed", "no_orm_model_dependency", "no_write_service_dependency", "migration_file_tests_defined", "worker_materialization_still_blocked"]:
        if precondition not in preconditions:
            fail(f"Radi144 Alembic revision implementation missing precondition: {precondition}")

    if "module_projections" in set(Base.metadata.tables):
        fail("module_projections table must remain absent in Alembic revision implementation decision gate")
    if PLANNED_REVISION_FILE.exists():
        fail("0008_module_projections.py must not exist in Alembic revision implementation decision gate")
    implementation_text = "\n".join([
        ENGINE_MODEL.read_text(encoding="utf-8"),
        WORKER_RUNTIME.read_text(encoding="utf-8"),
        ROUTE_FILE.read_text(encoding="utf-8"),
        "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py")),
    ])
    for token in FORBIDDEN_IMPLEMENTATION_TOKENS:
        if token in implementation_text:
            fail(f"Projection Alembic implementation must remain absent: {token}")

    for token in [
        "radi144_materialized_projection_alembic_revision_implementation_gate_decision",
        "status: alembic_revision_implementation_decision_recorded_no_file",
        "radi144_materialized_projection_migration_file_gate_decision",
        "safe_bundling_only_within_single_safety_boundary",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing Alembic revision implementation token: {token}")
    for blocker in ["alembic_projection_revision_file", "alembic_projection_migration", "module_projections_database_table", "materialized_projection_orm_model", "projection_write_service", "worker_projection_materialization"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["Planned revision file", "apps/api/alembic/versions/0008_module_projections.py", "radi144_materialized_projection_migration_file_gate_decision"]:
        if token not in decision_text:
            fail(f"Alembic revision implementation doc missing token: {token}")

    print("[OK] Radi144 materialized projection Alembic revision implementation decision is recorded")
    print("[OK] Revision file, migration, table, ORM model, write service, worker materialization, and route remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
