#!/usr/bin/env python3
"""Validate the Radi144 Result Persistence Gate Decision.

This is a no-go/deferral guard: result persistence is intentionally not opened
until the upstream engine job/API/projection gates are explicitly decided.
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
RESULT_SCHEMA = ROOT / "packages" / "contracts" / "results" / "radi144-result.schema.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_RESULT_PERSISTENCE_GATE_DECISION.md"
MIGRATIONS = ROOT / "apps" / "api" / "alembic" / "versions"

CORE_STORAGE_TABLES = {"module_runs", "module_results", "module_provenances"}
DEFERRED_STORAGE_TABLES = {"module_inputs", "module_outputs"}
ALLOWED_RADI144_RUNTIME_PATHS = {
    "/engines/radi144/jobs",
    "/engines/radi144/jobs/{job_id}",
    "/engines/radi144/jobs/{job_id}/result",
}
FORBIDDEN_ROUTE_FRAGMENTS = {"/engines", "/engine", "/modules", "/results", "/radi144"}
REQUIRED_BLOCKERS = {
    "result_persistence",
    "client_projection_builder",
    "engine_api",
    "worker_jobs",
    "engine_execution",
}
REQUIRED_PREREQUISITES = {
    "radi144_result_schema_gate",
    "radi144_engine_job_gate",
    "radi144_engine_api_gate",
    "radi144_client_projection_gate",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("result_schema_enabled") is not True:
        fail("Radi144 result schema must remain the prerequisite gate")
    for blocked_flag in ["result_persistence_enabled", "client_projection_enabled", "engine_api_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false after the persistence decision")

    if result_schema.get("properties", {}).get("retention", {}).get("type") != "object":
        fail("Radi144 result schema must retain retention metadata before persistence can open")
    if result_schema.get("properties", {}).get("client_projection", {}).get("type") != "object":
        fail("Radi144 result schema must retain the projection placeholder before persistence can open")

    storage_gate_opened = "radi144_result_persistence_storage_gate_decision" in project_text
    metadata_tables = set(Base.metadata.tables)
    if storage_gate_opened:
        missing_tables = sorted(CORE_STORAGE_TABLES - metadata_tables)
        if missing_tables:
            fail(f"Storage gate opened but core engine tables are missing: {missing_tables}")
    else:
        opened_tables = sorted(CORE_STORAGE_TABLES & metadata_tables)
        if opened_tables:
            fail(f"Engine persistence tables opened too early: {opened_tables}")
    deferred_tables = sorted(DEFERRED_STORAGE_TABLES & metadata_tables)
    if deferred_tables:
        fail(f"Deferred engine input/output tables opened too early: {deferred_tables}")

    migration_text = "\n".join(migration.read_text(encoding="utf-8") for migration in MIGRATIONS.glob("*.py"))
    for table in DEFERRED_STORAGE_TABLES:
        if table in migration_text:
            fail(f"Deferred engine input/output migration opened too early: {table}")

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    allowed_paths = ALLOWED_RADI144_RUNTIME_PATHS if "radi144_engine_api_runtime_route_gate_decision" in project_text else set()
    forbidden_paths = sorted(path for path in runtime_paths for fragment in FORBIDDEN_ROUTE_FRAGMENTS if fragment in path and path not in allowed_paths)
    if forbidden_paths:
        fail(f"Radi144 persistence decision must not open engine/result routes: {forbidden_paths}")

    for token in ["radi144_result_persistence_gate_decision", "status: deferred_until_upstream_engine_gates", "radi144_engine_job_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing persistence decision token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for prerequisite in REQUIRED_PREREQUISITES:
        if prerequisite not in decision_text:
            fail(f"Decision doc missing prerequisite: {prerequisite}")

    print("[OK] Radi144 persistence decision deferral is satisfied or superseded by storage-only gate")
    print("[OK] Engine input/output tables and runtime persistence remain blocked")
    print("[OK] Radi144 result/API/projection/workers/execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
