#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Alembic Revision Decision Gate."""

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
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-alembic-revision-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-alembic-revision-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_ALEMBIC_REVISION_DECISION_GATE.md"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"

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
    if runtime_scope.get("alembic_revision_decision_recorded") is not True:
        fail("Radi144 Alembic revision decision must be recorded")
    for flag in ["alembic_revision_file_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_alembic_revision_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-alembic-revision-decision.v1.instance.json":
        fail("Radi144 manifest must link Alembic revision decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 Alembic revision decision schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 Alembic revision decision boundary schema_id drift")
    if instance.get("decision") != "reserve_revision_plan_without_revision_file":
        fail("Radi144 Alembic revision decision must reserve plan only")
    if instance.get("planned_revision") != "0008_module_projections" or boundary.get("planned_revision") != "0008_module_projections":
        fail("Radi144 planned revision must be 0008_module_projections")
    if instance.get("required_future_gate") != "radi144_materialized_projection_alembic_revision_implementation_gate_decision":
        fail("Radi144 Alembic revision must point to revision implementation future gate")
    for flag in ["alembic_revision_file_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 Alembic revision {flag} must remain false")

    preconditions = set(instance.get("revision_preconditions", []))
    for precondition in ["ddl_implementation_decision_recorded", "revision_identifier_reserved", "depends_on_0007_engine_result_storage", "upgrade_downgrade_test_plan_defined", "sqlite_partial_index_strategy_finalized", "postgres_partial_index_strategy_finalized", "json_column_compatibility_finalized", "orm_model_still_blocked", "write_service_still_blocked"]:
        if precondition not in preconditions:
            fail(f"Radi144 Alembic revision missing precondition: {precondition}")

    if "module_projections" in set(Base.metadata.tables):
        fail("module_projections table must remain absent in Alembic revision decision gate")
    if (MIGRATIONS / "0008_module_projections.py").exists():
        fail("0008_module_projections.py must not exist in Alembic revision decision gate")
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
        "radi144_materialized_projection_alembic_revision_gate_decision",
        "status: alembic_revision_decision_recorded_no_revision_file",
        "radi144_materialized_projection_alembic_revision_implementation_gate_decision",
        "safe_bundling_only_within_single_safety_boundary",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing Alembic revision token: {token}")
    for blocker in ["alembic_projection_revision_file", "alembic_projection_migration", "module_projections_database_table", "materialized_projection_orm_model", "projection_write_service", "worker_projection_materialization"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["Planned revision", "0008_module_projections", "radi144_materialized_projection_alembic_revision_implementation_gate_decision"]:
        if token not in decision_text:
            fail(f"Alembic revision doc missing token: {token}")

    print("[OK] Radi144 materialized projection Alembic revision decision is recorded")
    print("[OK] Revision file, migration, table, ORM model, write service, worker materialization, and route remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
