#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Migration File Content Contract Decision Gate."""

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
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-migration-file-content-contract-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-migration-file-content-contract-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_MIGRATION_FILE_CONTENT_CONTRACT_DECISION_GATE.md"
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
REQUIRED_SECTIONS = {
    "module_docstring_with_gate_name",
    "revision_identifiers",
    "upgrade_function",
    "downgrade_function",
    "dialect_specific_index_notes",
}
REQUIRED_UPGRADE_STEPS = {
    "create_module_projections_table",
    "create_tenant_run_result_foreign_keys",
    "create_role_schema_raw_debug_check_constraints",
    "create_tenant_result_run_source_hash_indexes",
    "create_partial_unique_active_projection_index",
}
REQUIRED_DOWNGRADE_STEPS = {
    "drop_partial_unique_active_projection_index",
    "drop_projection_indexes",
    "drop_module_projections_table",
}
REQUIRED_FORBIDDEN_CONTENT = {
    "data_backfill",
    "module_result_payload_mutation",
    "orm_model_definition",
    "projection_write_service",
    "worker_materialization",
    "runtime_route",
    "raw_debug_payload_storage",
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
    if runtime_scope.get("migration_file_content_contract_decision_recorded") is not True:
        fail("Radi144 migration file content contract decision must be recorded")
    for flag in ["migration_file_enabled", "alembic_revision_file_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_migration_file_content_contract_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-migration-file-content-contract-decision.v1.instance.json":
        fail("Radi144 manifest must link migration file content contract decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 migration file content contract decision schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 migration file content contract decision boundary schema_id drift")
    if instance.get("decision") != "record_migration_file_content_contract_without_file_creation":
        fail("Radi144 migration file content contract must be recorded without file creation")
    if instance.get("planned_revision_file") != "apps/api/alembic/versions/0008_module_projections.py" or boundary.get("planned_revision_file") != "apps/api/alembic/versions/0008_module_projections.py":
        fail("Radi144 planned migration file path drift")
    if instance.get("planned_down_revision") != "0007_engine_result_storage" or boundary.get("planned_down_revision") != "0007_engine_result_storage":
        fail("Radi144 planned down revision must be 0007_engine_result_storage")
    if instance.get("required_future_gate") != "radi144_materialized_projection_migration_file_authoring_gate_decision":
        fail("Radi144 migration file content contract must point to migration file authoring future gate")
    if instance.get("migration_file_creation_allowed") is not False or boundary.get("migration_file_creation_allowed") is not False:
        fail("Radi144 migration file creation must remain disallowed")
    for flag in ["migration_file_enabled", "alembic_revision_file_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 migration file content contract {flag} must remain false")

    content_contract = instance.get("content_contract", {})
    sections = set(content_contract.get("required_sections", []))
    if not REQUIRED_SECTIONS.issubset(sections):
        fail(f"Radi144 migration file content contract missing sections: {sorted(REQUIRED_SECTIONS - sections)}")
    identifiers = content_contract.get("required_revision_identifiers", {})
    if identifiers.get("revision") != "0008_module_projections" or identifiers.get("down_revision") != "0007_engine_result_storage":
        fail("Radi144 migration file content revision identifiers drift")
    imports = set(content_contract.get("required_imports", []))
    if {"from alembic import op", "import sqlalchemy as sa"} - imports:
        fail("Radi144 migration file content contract missing required imports")
    upgrade_steps = set(content_contract.get("required_upgrade_steps", []))
    if not REQUIRED_UPGRADE_STEPS.issubset(upgrade_steps):
        fail(f"Radi144 migration file content contract missing upgrade steps: {sorted(REQUIRED_UPGRADE_STEPS - upgrade_steps)}")
    downgrade_steps = set(content_contract.get("required_downgrade_steps", []))
    if not REQUIRED_DOWNGRADE_STEPS.issubset(downgrade_steps):
        fail(f"Radi144 migration file content contract missing downgrade steps: {sorted(REQUIRED_DOWNGRADE_STEPS - downgrade_steps)}")
    forbidden_content = set(content_contract.get("forbidden_content", []))
    if not REQUIRED_FORBIDDEN_CONTENT.issubset(forbidden_content):
        fail(f"Radi144 migration file content contract missing forbidden content: {sorted(REQUIRED_FORBIDDEN_CONTENT - forbidden_content)}")

    if "module_projections" in set(Base.metadata.tables):
        fail("module_projections table must remain absent in migration file content contract decision gate")
    if PLANNED_MIGRATION_FILE.exists():
        fail("0008_module_projections.py must not exist in migration file content contract decision gate")
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
        "radi144_materialized_projection_migration_file_content_contract_gate_decision",
        "status: migration_file_content_contract_recorded_no_file",
        "radi144_materialized_projection_migration_file_authoring_gate_decision",
        "safe_bundling_only_within_single_safety_boundary",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing migration file content contract token: {token}")
    for blocker in ["migration_file", "alembic_projection_revision_file", "alembic_projection_migration", "module_projections_database_table", "materialized_projection_orm_model", "projection_write_service", "worker_projection_materialization"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["Required imports", "Required upgrade content", "radi144_materialized_projection_migration_file_authoring_gate_decision"]:
        if token not in decision_text:
            fail(f"Migration file content contract doc missing token: {token}")

    print("[OK] Radi144 materialized projection migration file content contract decision is recorded")
    print("[OK] Migration file, revision file, migration, table, ORM model, write service, worker materialization, and route remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
