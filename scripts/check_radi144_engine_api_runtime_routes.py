#!/usr/bin/env python3
"""Validate the Radi144 Engine API Runtime Route Gate.

This gate opens authenticated tenant-scoped FastAPI/OpenAPI route surfaces only.
The routes are non-executing and keep worker jobs, runtime result writes,
and engine execution blocked. The result route may be superseded by the
API Projection Read Gate, which requires the projection builder.
"""

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
API_BOUNDARY = ROOT / "packages" / "contracts" / "api" / "radi144-engine-api-boundary.v1.instance.json"
OPENAPI = ROOT / "packages" / "contracts" / "openapi" / "openapi.v1.json"
ROUTES = ROOT / "packages" / "contracts" / "routes" / "route-security-manifest.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_ENGINE_API_RUNTIME_ROUTE_GATE.md"

EXPECTED_ROUTES = {
    ("/engines/radi144/jobs", "POST"),
    ("/engines/radi144/jobs/{job_id}", "GET"),
    ("/engines/radi144/jobs/{job_id}/result", "GET"),
}
FORBIDDEN_RUNTIME_FILES = [
    ROOT / "apps" / "api" / "app" / "workers" / "radi144.py",
    ROOT / "apps" / "api" / "app" / "jobs" / "radi144.py",
]
REQUIRED_BLOCKERS = {"runtime_result_writes", "worker_runtime", "engine_execution"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    boundary = json.loads(API_BOUNDARY.read_text(encoding="utf-8"))
    openapi = json.loads(OPENAPI.read_text(encoding="utf-8"))
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("engine_api_runtime_routes_enabled") is not True:
        fail("Radi144 API runtime routes flag must be enabled")
    for blocked_flag in ["worker_jobs_enabled", "engine_execution_enabled", "result_persistence_enabled", "client_projection_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    if boundary.get("openapi_paths_enabled") is not True or boundary.get("runtime_routes_enabled") is not True:
        fail("Radi144 API boundary must mark OpenAPI/runtime routes enabled")
    for flag in ["engine_execution_enabled", "worker_jobs_enabled", "result_persistence_enabled", "client_projection_enabled"]:
        if boundary.get(flag) is not False:
            fail(f"API boundary must keep {flag} false")

    runtime = {
        (route.path, method)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in (route.methods or set())
        if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}
    }
    if not EXPECTED_ROUTES.issubset(runtime):
        fail(f"Runtime missing Radi144 routes: {sorted(EXPECTED_ROUTES - runtime)}")

    openapi_ops = {
        (path, method.upper())
        for path, methods in openapi.get("paths", {}).items()
        for method in methods
        if method.lower() in {"get", "post", "patch", "put", "delete"}
    }
    if not EXPECTED_ROUTES.issubset(openapi_ops):
        fail(f"OpenAPI missing Radi144 routes: {sorted(EXPECTED_ROUTES - openapi_ops)}")

    route_ops = {(route["path"], method) for route in routes.get("routes", []) for method in route.get("methods", [])}
    if not EXPECTED_ROUTES.issubset(route_ops):
        fail(f"Route manifest missing Radi144 routes: {sorted(EXPECTED_ROUTES - route_ops)}")
    for route in routes.get("routes", []):
        if route["path"].startswith("/engines/radi144"):
            if route.get("class") != "tenant":
                fail(f"Radi144 route must be tenant-classified: {route['path']}")
            constraints = set(route.get("constraints", []))
            required_constraints = ["tenant_context_required", "token_not_in_url", "no_worker_runtime", "no_engine_execution", "no_runtime_result_writes"]
            if route["path"] == "/engines/radi144/jobs/{job_id}/result":
                required_constraints.extend(["projection_builder_required", "no_raw_debug_output"])
            else:
                required_constraints.append("no_projection_builder")
            for required in required_constraints:
                if required not in constraints:
                    fail(f"Radi144 route {route['path']} missing constraint {required}")

    existing_runtime_files = [str(path.relative_to(ROOT)) for path in FORBIDDEN_RUNTIME_FILES if path.exists()]
    if existing_runtime_files:
        fail(f"Worker/job runtime files opened too early: {existing_runtime_files}")

    for token in ["radi144_engine_api_runtime_route_gate_decision", "status: runtime_routes_open_non_executing", "radi144_runtime_result_write_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing runtime route token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["non-executing", "runtime result writes remain blocked", "worker jobs remain blocked", "radi144_runtime_result_write_gate_decision"]:
        if token not in decision_text:
            fail(f"Runtime route doc missing token: {token}")

    print("[OK] Radi144 non-executing runtime API routes are classified and in OpenAPI")
    print("[OK] Routes remain tenant-scoped and token-in-URL safe")
    print("[OK] Worker jobs, runtime result writes, and execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
