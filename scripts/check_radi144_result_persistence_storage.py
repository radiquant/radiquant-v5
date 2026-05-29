#!/usr/bin/env python3
"""Validate the Radi144 Result Persistence Storage Gate.

This gate opens storage models/migrations only. It does not create runtime write
services, result APIs, projection builders, workers, or engine execution.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

import app.models  # noqa: F401,E402 - register ORM metadata
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
STORAGE_SCHEMA = ROOT / "packages" / "contracts" / "storage" / "radi144-result-storage.schema.v1.json"
STORAGE_INSTANCE = ROOT / "packages" / "contracts" / "storage" / "radi144-result-storage.v1.instance.json"
RESULT_SCHEMA = ROOT / "packages" / "contracts" / "results" / "radi144-result.schema.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_RESULT_PERSISTENCE_STORAGE_GATE.md"
MIGRATION = API_ROOT / "alembic" / "versions" / "0007_engine_result_storage.py"

REQUIRED_TABLES = {"module_runs", "module_results", "module_provenances"}
TENANT_SCOPED_TABLES = REQUIRED_TABLES
FORBIDDEN_TABLES = {"module_inputs", "module_outputs", "engine_jobs"}
FORBIDDEN_COLUMNS = {"raw_debug", "debug_json", "internal_state", "client_vector", "raw_resonance_matrix", "normalized_matrix"}
ALLOWED_RADI144_RUNTIME_PATHS = {
    "/engines/radi144/jobs",
    "/engines/radi144/jobs/{job_id}",
    "/engines/radi144/jobs/{job_id}/result",
}
FORBIDDEN_ROUTE_FRAGMENTS = {"/engines", "/engine", "/modules", "/results", "/radi144", "/jobs"}
REQUIRED_BLOCKERS = {
    "runtime_result_writes",
    "engine_api_runtime_routes",
    "client_projection_builder",
    "worker_jobs",
    "engine_execution",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    storage_schema = json.loads(STORAGE_SCHEMA.read_text(encoding="utf-8"))
    storage = json.loads(STORAGE_INSTANCE.read_text(encoding="utf-8"))
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("result_persistence_storage_enabled") is not True:
        fail("Radi144 result persistence storage flag must be enabled")
    for blocked_flag in ["result_persistence_enabled", "engine_api_enabled", "worker_jobs_enabled", "engine_execution_enabled", "client_projection_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    boundary = manifest.get("storage_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/storage/radi144-result-storage.v1.instance.json":
        fail("Radi144 manifest must link storage boundary instance")
    if storage_schema.get("properties", {}).get("schema_id", {}).get("const") != storage.get("schema_id"):
        fail("Radi144 storage schema_id drift")
    if storage.get("status") != "storage_model_initialized_runtime_writes_blocked":
        fail("Radi144 storage status drift")
    if storage.get("storage_enabled") is not True or storage.get("runtime_writes_enabled") is not False:
        fail("Storage gate must enable models but keep runtime writes blocked")
    if set(storage.get("tables", [])) != REQUIRED_TABLES:
        fail("Storage boundary must list only core storage tables")

    tables = set(Base.metadata.tables)
    missing = sorted(REQUIRED_TABLES - tables)
    if missing:
        fail(f"Missing storage tables in metadata: {missing}")
    forbidden_tables = sorted(FORBIDDEN_TABLES & tables)
    if forbidden_tables:
        fail(f"Forbidden runtime/job/input-output tables opened: {forbidden_tables}")

    for table_name in TENANT_SCOPED_TABLES:
        table = Base.metadata.tables[table_name]
        if "tenant_id" not in table.columns:
            fail(f"Storage table lacks tenant_id: {table_name}")
        forbidden_columns = sorted(FORBIDDEN_COLUMNS & set(table.columns))
        if forbidden_columns:
            fail(f"Storage table exposes forbidden raw/debug columns in {table_name}: {forbidden_columns}")

    module_runs = Base.metadata.tables["module_runs"]
    for column in ["tenant_id", "session_id", "workflow_run_id", "workflow_step_run_id", "module_id", "phase", "status", "schema_id", "job_contract_schema_id"]:
        if column not in module_runs.columns:
            fail(f"module_runs missing column: {column}")

    module_results = Base.metadata.tables["module_results"]
    for column in ["tenant_id", "module_run_id", "schema_id", "result_payload_json", "retention_json", "projection_status", "raw_debug_allowed", "client_projection_required"]:
        if column not in module_results.columns:
            fail(f"module_results missing column: {column}")

    module_provenances = Base.metadata.tables["module_provenances"]
    for column in ["tenant_id", "module_run_id", "algorithm_version", "manifest_version", "input_hash", "reference_matrix_version", "compute_backend", "duration_ms", "provenance_json"]:
        if column not in module_provenances.columns:
            fail(f"module_provenances missing column: {column}")

    if result_schema.get("properties", {}).get("retention", {}).get("type") != "object":
        fail("Radi144 result schema must keep retention metadata")
    if result_schema.get("properties", {}).get("client_projection", {}).get("properties", {}).get("status", {}).get("enum") != ["pending_projection_builder"]:
        fail("Radi144 result schema must keep projection placeholder pending")

    if not MIGRATION.is_file():
        fail("Missing engine result storage migration")
    migration_text = MIGRATION.read_text(encoding="utf-8")
    for table_name in REQUIRED_TABLES:
        if table_name not in migration_text:
            fail(f"Storage migration missing table: {table_name}")
    for forbidden in FORBIDDEN_TABLES:
        if forbidden in migration_text:
            fail(f"Storage migration contains forbidden runtime table token: {forbidden}")
    for forbidden in FORBIDDEN_COLUMNS:
        if f'\"{forbidden}\"' in migration_text:
            fail(f"Storage migration contains forbidden raw/debug column: {forbidden}")

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    allowed_paths = ALLOWED_RADI144_RUNTIME_PATHS if "radi144_engine_api_runtime_route_gate_decision" in project_text else set()
    forbidden_paths = sorted(path for path in runtime_paths for fragment in FORBIDDEN_ROUTE_FRAGMENTS if fragment in path and path not in allowed_paths)
    if forbidden_paths:
        fail(f"Storage gate must not open engine/result routes: {forbidden_paths}")

    for token in ["radi144_result_persistence_storage_gate_decision", "status: storage_model_initialized_runtime_writes_blocked", "radi144_engine_api_runtime_route_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing storage gate token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["storage-only", "runtime writes remain blocked", "engine execution remains blocked", "radi144_engine_api_runtime_route_gate_decision"]:
        if token not in decision_text:
            fail(f"Storage doc missing token: {token}")

    print("[OK] Radi144 result storage models and migration are present")
    print("[OK] ModuleRun/ModuleResult/ModuleProvenance are tenant-scoped with retention/provenance invariants")
    print("[OK] Runtime writes, API routes, projection builder, workers, and execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
