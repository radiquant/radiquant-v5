#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Table Contract Decision Gate."""

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
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-table-contract-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-table-contract-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_TABLE_CONTRACT_DECISION_GATE.md"
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

REQUIRED_COLUMNS = {
    "id",
    "tenant_id",
    "module_run_id",
    "module_result_id",
    "role",
    "projection_schema_id",
    "projection_builder_version",
    "source_result_hash",
    "projection_payload_json",
    "retention_json",
    "invalidated_at",
    "created_at",
    "updated_at",
}

FORBIDDEN_COLUMNS = {
    "raw_payload_json",
    "debug_payload_json",
    "internal_payload_json",
    "client_vector_json",
    "raw_resonance_matrix_json",
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
    if runtime_scope.get("table_contract_decision_recorded") is not True:
        fail("Radi144 table contract decision must be recorded")
    for flag in ["alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_table_contract_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-table-contract-decision.v1.instance.json":
        fail("Radi144 manifest must link table contract decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 table contract decision schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 table contract decision boundary schema_id drift")
    if instance.get("decision") != "record_table_contract_without_ddl_implementation":
        fail("Radi144 table contract must be recorded without DDL implementation")
    if instance.get("planned_table") != "module_projections" or boundary.get("planned_table") != "module_projections":
        fail("Radi144 planned table must remain module_projections")
    if instance.get("required_future_gate") != "radi144_materialized_projection_table_ddl_implementation_gate_decision":
        fail("Radi144 table contract must point to DDL implementation future gate")
    for flag in ["alembic_migration_enabled", "projection_storage_tables_enabled", "orm_model_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 table contract {flag} must remain false")

    table_contract = instance.get("table_contract", {})
    columns = {item.get("name") for item in table_contract.get("columns", [])}
    missing_columns = REQUIRED_COLUMNS - columns
    if missing_columns:
        fail(f"Radi144 table contract missing columns: {sorted(missing_columns)}")
    forbidden_columns = set(table_contract.get("forbidden_columns", []))
    if not FORBIDDEN_COLUMNS.issubset(forbidden_columns):
        fail(f"Radi144 table contract missing forbidden columns: {sorted(FORBIDDEN_COLUMNS - forbidden_columns)}")
    for bad_column in FORBIDDEN_COLUMNS:
        if bad_column in columns:
            fail(f"Radi144 table contract must not define forbidden column: {bad_column}")
    fks = {(item.get("column"), item.get("references"), item.get("on_delete")) for item in table_contract.get("foreign_keys", [])}
    for fk in [("tenant_id", "tenants.id", "RESTRICT"), ("module_run_id", "module_runs.id", "CASCADE"), ("module_result_id", "module_results.id", "CASCADE")]:
        if fk not in fks:
            fail(f"Radi144 table contract missing FK: {fk}")
    constraints = {item.get("name") for item in table_contract.get("constraints", [])}
    for constraint in ["pk_module_projections", "ck_module_projections_role", "ck_module_projections_schema_id", "uq_module_projections_active_role", "ck_module_projections_no_raw_debug"]:
        if constraint not in constraints:
            fail(f"Radi144 table contract missing constraint: {constraint}")

    if "module_projections" in set(Base.metadata.tables):
        fail("module_projections table must remain absent in table contract decision gate")
    implementation_text = "\n".join([
        ENGINE_MODEL.read_text(encoding="utf-8"),
        WORKER_RUNTIME.read_text(encoding="utf-8"),
        ROUTE_FILE.read_text(encoding="utf-8"),
        "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py")),
    ])
    for token in FORBIDDEN_IMPLEMENTATION_TOKENS:
        if token in implementation_text:
            fail(f"Projection table implementation must remain absent: {token}")

    for token in [
        "radi144_materialized_projection_table_contract_gate_decision",
        "status: table_contract_recorded_no_table",
        "radi144_materialized_projection_table_ddl_implementation_gate_decision",
        "safe_bundling_only_within_single_safety_boundary",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing table contract token: {token}")
    for blocker in ["alembic_projection_migration", "module_projections_database_table", "materialized_projection_orm_model", "projection_write_service", "worker_projection_materialization"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["planned `module_projections` table contract", "Active uniqueness", "radi144_materialized_projection_table_ddl_implementation_gate_decision"]:
        if token not in decision_text:
            fail(f"Table contract doc missing token: {token}")

    print("[OK] Radi144 materialized projection table contract decision is recorded")
    print("[OK] Table, Alembic revision, ORM model, write service, worker materialization, and route remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
