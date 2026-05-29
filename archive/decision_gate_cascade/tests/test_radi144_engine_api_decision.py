"""Radi144 Engine API Gate Decision tests.

The gate decides the future tenant-scoped endpoint boundary but does not add
OpenAPI paths, route-manifest entries, or runtime FastAPI routes yet.
"""

import json
from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
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


def test_api_decision_sets_boundary_without_enabling_runtime_scope() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scope = manifest["runtime_scope"]

    assert scope["engine_api_boundary_decided"] is True
    assert scope["engine_api_enabled"] is False
    assert scope["worker_jobs_enabled"] is False
    assert scope["engine_execution_enabled"] is False
    assert scope["result_persistence_enabled"] is False
    assert scope["client_projection_enabled"] is False


def test_api_boundary_records_planned_tenant_endpoints() -> None:
    boundary = json.loads(API_BOUNDARY.read_text(encoding="utf-8"))
    endpoints = {(item["method"], item["path"]) for item in boundary["planned_endpoints"]}

    assert boundary["schema_id"] == "radi144_engine_api_boundary_v1"
    assert boundary["status"] == "decision_only_not_opened"
    assert boundary["route_class"] == "tenant"
    assert boundary["auth_required"] is True
    assert boundary["tenant_guard_required"] is True
    assert endpoints == PLANNED_ENDPOINTS
    assert all(item["opens_runtime_execution"] is False for item in boundary["planned_endpoints"])


def test_api_boundary_matches_openapi_route_manifest_for_current_gate() -> None:
    openapi = json.loads(OPENAPI.read_text(encoding="utf-8"))
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    openapi_paths = set(openapi["paths"])
    route_pairs = {(route["path"], method) for route in routes["routes"] for method in route["methods"]}
    runtime_route_gate_opened = "radi144_engine_api_runtime_route_gate_decision" in PROJECT_ANCHOR.read_text(encoding="utf-8")

    for method, path in PLANNED_ENDPOINTS:
        assert (path in openapi_paths) is runtime_route_gate_opened
        assert ((path, method) in route_pairs) is runtime_route_gate_opened


def test_api_boundary_runtime_routes_match_current_gate() -> None:
    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    runtime_route_gate_opened = "radi144_engine_api_runtime_route_gate_decision" in PROJECT_ANCHOR.read_text(encoding="utf-8")

    for _method, path in PLANNED_ENDPOINTS:
        assert (path in runtime_paths) is runtime_route_gate_opened


def test_api_boundary_preserves_security_and_language_invariants() -> None:
    boundary = json.loads(API_BOUNDARY.read_text(encoding="utf-8"))
    invariants = boundary["security_invariants"]

    assert invariants["unclassified_route_fails_ci"] is True
    assert invariants["frontend_route_requires_openapi_contract"] is True
    assert invariants["token_in_url_allowed"] is False
    assert invariants["wellbeing_language_only"] is True
    assert invariants["medical_claims_allowed"] is False


def test_project_anchor_and_decision_doc_advance_to_projection_decision() -> None:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    assert "radi144_engine_api_gate_decision:" in project_text
    assert "status: decision_only_boundary_not_opened" in project_text
    assert "radi144_client_projection_gate_decision" in project_text
    for blocker in ["engine_api", "worker_jobs", "engine_execution", "result_persistence", "client_projection_builder"]:
        assert f"- {blocker}" in project_text
    for token in ["decision-only", "OpenAPI paths remain closed", "runtime FastAPI routes remain closed"]:
        assert token in decision_text
