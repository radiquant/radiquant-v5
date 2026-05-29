#!/usr/bin/env python3
"""Validate the Radi144 Engine API Gate Decision.

This gate records the future tenant-scoped API boundary but intentionally does
not add OpenAPI paths or runtime FastAPI routes yet.
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
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_ENGINE_API_GATE_DECISION.md"

PLANNED_ENDPOINTS = {
    ("POST", "/engines/radi144/jobs"),
    ("GET", "/engines/radi144/jobs/{job_id}"),
    ("GET", "/engines/radi144/jobs/{job_id}/result"),
}
FORBIDDEN_RUNTIME_FRAGMENTS = {"/engines", "/engine", "/modules", "/results", "/radi144", "/jobs"}
REQUIRED_BLOCKERS = {
    "engine_api",
    "worker_jobs",
    "engine_execution",
    "result_persistence",
    "client_projection_builder",
}


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
    if runtime_scope.get("engine_api_boundary_decided") is not True:
        fail("Radi144 API boundary decision flag must be set")
    for blocked_flag in ["engine_api_enabled", "worker_jobs_enabled", "engine_execution_enabled", "result_persistence_enabled", "client_projection_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    api_boundary = manifest.get("api_boundary", {})
    if api_boundary.get("instance_path") != "packages/contracts/api/radi144-engine-api-boundary.v1.instance.json":
        fail("Radi144 manifest must link the API boundary instance")
    if boundary.get("status") != "decision_only_not_opened":
        fail("Radi144 API boundary must remain decision-only")
    runtime_route_gate_opened = "radi144_engine_api_runtime_route_gate_decision" in project_text
    if runtime_route_gate_opened:
        if boundary.get("openapi_paths_enabled") is not True or boundary.get("runtime_routes_enabled") is not True:
            fail("API boundary must mark OpenAPI/runtime routes enabled after route gate")
    else:
        for flag in ["openapi_paths_enabled", "runtime_routes_enabled"]:
            if boundary.get(flag) is not False:
                fail(f"API boundary flag must remain false before runtime route gate: {flag}")
    for flag in ["engine_execution_enabled", "worker_jobs_enabled", "result_persistence_enabled", "client_projection_enabled"]:
        if boundary.get(flag) is not False:
            fail(f"API boundary flag must remain false: {flag}")

    boundary_endpoints = {(item["method"], item["path"]) for item in boundary.get("planned_endpoints", [])}
    if boundary_endpoints != PLANNED_ENDPOINTS:
        fail(f"Radi144 planned endpoints drift: {sorted(boundary_endpoints)}")
    if any(item.get("opens_runtime_execution") is not False for item in boundary.get("planned_endpoints", [])):
        fail("Planned API endpoints must not open runtime execution")

    openapi_paths = set(openapi.get("paths", {}))
    route_pairs = {(route["path"], method) for route in routes.get("routes", []) for method in route.get("methods", [])}
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    if runtime_route_gate_opened:
        for method, path in PLANNED_ENDPOINTS:
            if path not in openapi_paths:
                fail(f"Radi144 API path missing from OpenAPI after route gate: {path}")
            if (path, method) not in route_pairs:
                fail(f"Radi144 API route missing from route manifest after route gate: {method} {path}")
            if path not in runtime_paths:
                fail(f"Radi144 API runtime route missing after route gate: {path}")
    else:
        for method, path in PLANNED_ENDPOINTS:
            if path in openapi_paths:
                fail(f"Radi144 API path entered OpenAPI too early: {path}")
            if (path, method) in route_pairs:
                fail(f"Radi144 API route entered route manifest too early: {method} {path}")
        forbidden_runtime = sorted(path for path in runtime_paths for fragment in FORBIDDEN_RUNTIME_FRAGMENTS if fragment in path)
        if forbidden_runtime:
            fail(f"Radi144 API runtime route opened too early: {forbidden_runtime}")

    invariants = boundary.get("security_invariants", {})
    if invariants.get("unclassified_route_fails_ci") is not True:
        fail("API boundary must preserve unclassified-route CI failure")
    if invariants.get("frontend_route_requires_openapi_contract") is not True:
        fail("API boundary must preserve frontend OpenAPI requirement")
    if invariants.get("token_in_url_allowed") is not False:
        fail("API boundary must forbid URL tokens")
    if invariants.get("medical_claims_allowed") is not False:
        fail("API boundary must forbid medical claims")

    for token in ["radi144_engine_api_gate_decision", "status: decision_only_boundary_not_opened", "radi144_client_projection_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing API decision token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["decision-only", "OpenAPI paths remain closed", "runtime FastAPI routes remain closed", "radi144_client_projection_gate_decision"]:
        if token not in decision_text:
            fail(f"Decision doc missing token: {token}")

    print("[OK] Radi144 API boundary decision is satisfied or superseded by runtime route gate")
    print("[OK] Radi144 OpenAPI, route-manifest, and runtime route state match the current gate")
    print("[OK] Engine execution, workers, persistence, and projection builder remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
