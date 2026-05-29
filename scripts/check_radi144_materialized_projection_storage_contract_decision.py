#!/usr/bin/env python3
"""Validate the Radi144 Materialized Projection Storage Contract Decision Gate."""

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
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-storage-contract-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-materialized-projection-storage-contract-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_MATERIALIZED_PROJECTION_STORAGE_CONTRACT_DECISION_GATE.md"
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
    if runtime_scope.get("materialized_projection_storage_contract_recorded") is not True:
        fail("Radi144 materialized projection storage contract must be recorded")
    if runtime_scope.get("api_projection_reads_enabled") is not True:
        fail("Radi144 API projection reads must remain enabled")
    for flag in [
        "materialized_projection_storage_enabled",
        "projection_storage_tables_enabled",
        "projection_write_service_enabled",
        "worker_projection_materialization_enabled",
    ]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("materialized_projection_storage_contract_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-materialized-projection-storage-contract-decision.v1.instance.json":
        fail("Radi144 manifest must link materialized projection storage contract decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 materialized projection storage contract schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 materialized projection storage contract boundary schema_id drift")
    if instance.get("decision") != "record_storage_contract_without_storage_implementation":
        fail("Radi144 storage contract must not enable implementation")
    if instance.get("planned_storage_entity") != "module_projections":
        fail("Radi144 storage contract must plan module_projections entity")
    if instance.get("required_future_gate") != "radi144_materialized_projection_storage_schema_gate_decision":
        fail("Radi144 storage contract must point to schema future gate")
    for flag in [
        "materialized_projection_storage_enabled",
        "projection_storage_tables_enabled",
        "projection_write_service_enabled",
        "worker_projection_materialization_enabled",
    ]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 storage contract {flag} must remain false")

    required_fields = set(instance.get("required_contract_fields", []))
    for field in ["tenant_id", "module_run_id", "module_result_id", "role", "projection_schema_id", "source_result_hash", "retention_json", "projection_payload_json", "invalidated_at"]:
        if field not in required_fields:
            fail(f"Radi144 storage contract missing required field: {field}")
    forbidden_fields = set(instance.get("forbidden_contract_fields", []))
    for field in ["raw_debug", "debug_json", "internal_state", "client_vector", "raw_resonance_matrix", "normalized_matrix"]:
        if field not in forbidden_fields:
            fail(f"Radi144 storage contract missing forbidden field: {field}")

    tables = set(Base.metadata.tables)
    if "module_projections" in tables:
        fail("module_projections table must remain absent in contract-only gate")

    implementation_text = "\n".join(
        [
            ENGINE_MODEL.read_text(encoding="utf-8"),
            WORKER_RUNTIME.read_text(encoding="utf-8"),
            ROUTE_FILE.read_text(encoding="utf-8"),
            "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py")),
        ]
    )
    for token in FORBIDDEN_IMPLEMENTATION_TOKENS:
        if token in implementation_text:
            fail(f"Projection storage implementation must remain absent: {token}")

    route_text = ROUTE_FILE.read_text(encoding="utf-8")
    for required in ["Radi144ProjectionBuilder", "result_payload_json", "Radi144Result.model_validate"]:
        if required not in route_text:
            fail(f"API projection route must remain on-demand: {required}")

    for token in [
        "radi144_materialized_projection_storage_contract_gate_decision",
        "status: storage_contract_recorded_storage_disabled",
        "radi144_materialized_projection_storage_schema_gate_decision",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing storage contract token: {token}")
    for blocker in [
        "materialized_projection_storage_table",
        "projection_storage_migration",
        "projection_write_service",
        "worker_projection_materialization",
        "raw_debug_projection_storage",
    ]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["contract without creating storage implementation", "module_projections", "radi144_materialized_projection_storage_schema_gate_decision"]:
        if token not in decision_text:
            fail(f"Storage contract doc missing token: {token}")

    print("[OK] Radi144 materialized projection storage contract is recorded")
    print("[OK] No projection table, migration, write service, worker materialization, or route was opened")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
