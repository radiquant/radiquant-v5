"""Radi144 Engine API Runtime Route Gate tests."""

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
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_ENGINE_API_RUNTIME_ROUTE_GATE.md"

EXPECTED_ROUTES = {
    ("/engines/radi144/jobs", "POST"),
    ("/engines/radi144/jobs/{job_id}", "GET"),
    ("/engines/radi144/jobs/{job_id}/result", "GET"),
}


def test_runtime_route_gate_opens_only_non_executing_api_surface() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    boundary = json.loads(API_BOUNDARY.read_text(encoding="utf-8"))

    assert manifest["runtime_scope"]["engine_api_runtime_routes_enabled"] is True
    assert boundary["openapi_paths_enabled"] is True
    assert boundary["runtime_routes_enabled"] is True
    assert manifest["runtime_scope"]["worker_jobs_enabled"] is False
    assert manifest["runtime_scope"]["engine_execution_enabled"] is False
    assert manifest["runtime_scope"]["result_persistence_enabled"] is False
    assert manifest["runtime_scope"]["client_projection_enabled"] is False


def test_radi144_routes_are_registered_in_runtime_openapi_and_manifest() -> None:
    runtime = {
        (route.path, method)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in (route.methods or set())
        if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}
    }
    openapi = json.loads(OPENAPI.read_text(encoding="utf-8"))
    openapi_ops = {
        (path, method.upper())
        for path, methods in openapi["paths"].items()
        for method in methods
        if method.lower() in {"get", "post", "patch", "put", "delete"}
    }
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    route_ops = {(route["path"], method) for route in routes["routes"] for method in route["methods"]}

    assert EXPECTED_ROUTES.issubset(runtime)
    assert EXPECTED_ROUTES.issubset(openapi_ops)
    assert EXPECTED_ROUTES.issubset(route_ops)


def test_radi144_routes_are_tenant_classified_and_non_executing() -> None:
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    radi144_routes = [route for route in routes["routes"] if route["path"].startswith("/engines/radi144")]

    assert len(radi144_routes) == 3
    for route in radi144_routes:
        assert route["class"] == "tenant"
        constraints = set(route["constraints"])
        required_constraints = ["tenant_context_required", "token_not_in_url", "no_worker_runtime", "no_engine_execution", "no_runtime_result_writes"]
        if route["path"] == "/engines/radi144/jobs/{job_id}/result":
            required_constraints.extend(["projection_builder_required", "no_raw_debug_output"])
        else:
            required_constraints.append("no_projection_builder")
        for required in required_constraints:
            assert required in constraints


def test_radi144_runtime_route_handlers_are_non_executing() -> None:
    route_names = {route.name for route in app.routes if isinstance(route, APIRoute) and route.path.startswith("/engines/radi144")}

    assert route_names == {
        "create_radi144_job_record",
        "get_radi144_job_boundary_status",
        "get_radi144_projected_result",
    }
    assert not (ROOT / "apps/api/app/workers/radi144.py").exists()
    assert not (ROOT / "apps/api/app/jobs/radi144.py").exists()


def test_project_anchor_and_doc_advance_to_runtime_result_write_decision() -> None:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    assert "radi144_engine_api_runtime_route_gate_decision:" in project_text
    assert "status: runtime_routes_open_non_executing" in project_text
    assert "radi144_runtime_result_write_gate_decision" in project_text
    for blocker in ["runtime_result_writes", "client_projection_builder", "worker_runtime", "engine_execution"]:
        assert f"- {blocker}" in project_text
    for token in ["non-executing", "runtime result writes remain blocked", "worker jobs remain blocked"]:
        assert token in decision_text
