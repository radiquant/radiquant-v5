#!/usr/bin/env python3
"""Validate the Radi144 API Projection Read Gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
BUILDER_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-projection-builder.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_API_PROJECTION_READ_GATE.md"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
REQUIRED_BLOCKERS = {"worker_runtime", "engine_execution"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    builder = json.loads(BUILDER_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("api_projection_reads_enabled") is not True:
        fail("Radi144 API projection reads flag must be enabled")
    for blocked_flag in ["worker_jobs_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")
    if builder.get("api_projection_reads_enabled") is not True:
        fail("Projection builder boundary must allow API projection reads")

    runtime_routes = {(route.path, method) for route in app.routes if isinstance(route, APIRoute) for method in (route.methods or set())}
    if ("/engines/radi144/jobs/{job_id}/result", "GET") not in runtime_routes:
        fail("Radi144 projected result route must be present")

    route_text = ROUTE_FILE.read_text(encoding="utf-8")
    for token in ["Radi144ProjectionBuilder", "ModuleRun", "result_payload_json", "role", "Radi144Result.model_validate"]:
        if token not in route_text:
            fail(f"Projection read route missing token: {token}")
    for forbidden in ["Radi144ResultWriter", "persist_result", "Radi144DomainService", "build_plan"]:
        if forbidden in route_text:
            fail(f"Projection read route must not write or execute: {forbidden}")

    for token in ["radi144_api_projection_read_gate_decision", "status: api_projection_reads_enabled", "radi144_worker_job_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing API projection read token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["projection reads", "no raw/debug/internal data", "worker jobs remain blocked", "engine execution remains blocked", "radi144_worker_job_gate_decision"]:
        if token not in decision_text:
            fail(f"Projection read doc missing token: {token}")

    print("[OK] Radi144 API projection reads are enabled through the projection builder")
    print("[OK] Result route reads stored payloads without raw/debug/internal exposure")
    print("[OK] Worker runtime and engine execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
