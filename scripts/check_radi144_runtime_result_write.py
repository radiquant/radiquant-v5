#!/usr/bin/env python3
"""Validate the Radi144 Runtime Result Write Gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402
from app.services.radi144 import Radi144ResultWriter  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
WRITE_SCHEMA = ROOT / "packages" / "contracts" / "storage" / "radi144-runtime-result-write.schema.v1.json"
WRITE_INSTANCE = ROOT / "packages" / "contracts" / "storage" / "radi144-runtime-result-write.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_RUNTIME_RESULT_WRITE_GATE.md"
SERVICE = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "result_writer.py"
FORBIDDEN_RUNTIME_FILES = [ROOT / "apps" / "api" / "app" / "workers" / "radi144.py", ROOT / "apps" / "api" / "app" / "jobs" / "radi144.py"]
REQUIRED_BLOCKERS = {"api_result_writes", "client_projection_builder", "worker_jobs", "engine_execution"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    write_schema = json.loads(WRITE_SCHEMA.read_text(encoding="utf-8"))
    write = json.loads(WRITE_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("runtime_result_write_service_enabled") is not True:
        fail("Radi144 runtime result write service flag must be enabled")
    for blocked_flag in ["worker_jobs_enabled", "engine_execution_enabled", "client_projection_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    boundary = manifest.get("runtime_result_write_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/storage/radi144-runtime-result-write.v1.instance.json":
        fail("Radi144 manifest must link runtime result write boundary")
    if write_schema.get("properties", {}).get("schema_id", {}).get("const") != write.get("schema_id"):
        fail("Radi144 runtime result write schema_id drift")
    if write.get("write_service_enabled") is not True:
        fail("Radi144 result write service must be enabled")
    for flag in ["api_result_writes_enabled", "worker_jobs_enabled", "engine_execution_enabled", "projection_builder_enabled"]:
        if write.get(flag) is not False:
            fail(f"Radi144 runtime result write boundary must keep {flag} false")

    if not SERVICE.is_file() or Radi144ResultWriter is None:
        fail("Radi144 result writer service is not importable")
    service_text = SERVICE.read_text(encoding="utf-8")
    for token in ["WorkflowStepRun", "ModuleRun", "ModuleResult", "ModuleProvenance", "raw_debug_must_remain_forbidden", "await self.session.flush()"]:
        if token not in service_text:
            fail(f"Radi144 result writer missing invariant token: {token}")
    if "await self.session.commit()" in service_text:
        fail("Radi144 result writer must not commit transactions internally")

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    expected_routes = {"/engines/radi144/jobs", "/engines/radi144/jobs/{job_id}", "/engines/radi144/jobs/{job_id}/result"}
    if not expected_routes.issubset(runtime_paths):
        fail("Radi144 API runtime routes must remain present")
    existing_runtime_files = [str(path.relative_to(ROOT)) for path in FORBIDDEN_RUNTIME_FILES if path.exists()]
    if existing_runtime_files:
        fail(f"Worker/job runtime files opened too early: {existing_runtime_files}")

    for token in ["radi144_runtime_result_write_gate_decision", "status: write_service_enabled_not_wired_to_api_or_workers", "radi144_projection_builder_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing runtime write token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["service-only", "not wired to API routes", "worker jobs remain blocked", "engine execution remains blocked", "radi144_projection_builder_gate_decision"]:
        if token not in decision_text:
            fail(f"Runtime write doc missing token: {token}")

    print("[OK] Radi144 runtime result write service is enabled and contract-bound")
    print("[OK] Writer preserves tenant workflow-step, retention, provenance, and raw-debug guards")
    print("[OK] API result writes, projection builder, workers, and execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
