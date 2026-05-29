#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Relationship Contract Decision Gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401,E402 - register ORM metadata
from app.db.base import Base  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-relationship-contract-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-relationship-contract-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_RELATIONSHIP_CONTRACT_DECISION_GATE.md"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"

FORBIDDEN_IMPLEMENTATION_TOKENS = {
    "class ModuleProjection",
    "__tablename__ = \"module_projections\"",
    "op.create_table(\"module_projections\"",
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
    if runtime_scope.get("relationship_contract_recorded") is not True:
        fail("Radi144 relationship contract decision must be recorded")
    for flag in ["orm_model_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_relationship_contract_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-relationship-contract-decision.v1.instance.json":
        fail("Radi144 manifest must link relationship contract decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 relationship contract schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 relationship contract boundary schema_id drift")
    if instance.get("decision") != "record_relationship_contract_before_orm_model":
        fail("Radi144 relationship contract decision must precede ORM model")
    if instance.get("required_future_gate") != "radi144_materialized_projection_constraints_gate_decision":
        fail("Radi144 relationship contract must point to constraints future gate")
    for flag in ["orm_model_enabled", "alembic_migration_enabled", "projection_storage_tables_enabled", "projection_write_service_enabled", "worker_projection_materialization_enabled"]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 relationship contract {flag} must remain false")

    relationships = {item.get("name"): item for item in instance.get("planned_relationships", []) if isinstance(item, dict)}
    expected = {
        "tenant": ("module_projections.tenant_id", "tenants.id", "RESTRICT"),
        "module_run": ("module_projections.module_run_id", "module_runs.id", "CASCADE"),
        "module_result": ("module_projections.module_result_id", "module_results.id", "CASCADE"),
    }
    for name, (source, target, on_delete) in expected.items():
        relationship = relationships.get(name)
        if relationship is None:
            fail(f"Missing planned relationship: {name}")
            continue
        if relationship.get("source") != source or relationship.get("target") != target or relationship.get("on_delete") != on_delete:
            fail(f"Relationship drift for {name}")
    constraints = set(instance.get("planned_constraints", []))
    for constraint in ["tenant_id_required", "module_run_id_required", "module_result_id_required", "role_in_client_therapist", "source_result_hash_required", "unique_active_projection_per_module_result_role"]:
        if constraint not in constraints:
            fail(f"Radi144 relationship contract missing constraint: {constraint}")

    if "module_projections" in set(Base.metadata.tables):
        fail("module_projections table must remain absent in relationship contract gate")
    implementation_text = "\n".join([
        ENGINE_MODEL.read_text(encoding="utf-8"),
        WORKER_RUNTIME.read_text(encoding="utf-8"),
        ROUTE_FILE.read_text(encoding="utf-8"),
        "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py")),
    ])
    for token in FORBIDDEN_IMPLEMENTATION_TOKENS:
        if token in implementation_text:
            fail(f"Projection storage implementation must remain absent: {token}")

    for token in [
        "radi144_materialized_projection_relationship_contract_gate_decision",
        "status: relationship_contract_recorded_model_disabled",
        "radi144_materialized_projection_constraints_gate_decision",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing relationship contract token: {token}")
    for blocker in [
        "materialized_projection_orm_model",
        "alembic_projection_migration",
        "materialized_projection_storage_table",
        "projection_write_service",
        "worker_projection_materialization",
    ]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["No SQLAlchemy model", "module_projections.tenant_id -> tenants.id", "radi144_materialized_projection_constraints_gate_decision"]:
        if token not in decision_text:
            fail(f"Relationship contract doc missing token: {token}")

    print("[OK] Radi144 materialized projection relationship contract is recorded")
    print("[OK] No ORM model, migration, table, write service, worker materialization, or route was opened")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
