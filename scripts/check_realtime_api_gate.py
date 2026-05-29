#!/usr/bin/env python3
"""Validate the Realtime API Gate without opening job tracker or engine execution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402
from app.schemas.realtime import EventReplayResponse  # noqa: E402

EVENT_REGISTRY = ROOT / "packages" / "contracts" / "events" / "event-registry.v1.json"
ROUTE_MANIFEST = ROOT / "packages" / "contracts" / "routes" / "route-security-manifest.v1.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
REQUIRED_REALTIME_ROUTES = {
    ("/sessions/{session_id}/events", "GET"),
    ("/sessions/{session_id}/events/stream", "GET"),
}
FORBIDDEN_PATH_FRAGMENTS = {"/jobs", "/engines", "/engine", "/modules", "/results", "/workflow-ui"}
ALLOWED_RADI144_RUNTIME_PATHS = {
    "/engines/radi144/jobs",
    "/engines/radi144/jobs/{job_id}",
    "/engines/radi144/jobs/{job_id}/result",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    registry = json.loads(EVENT_REGISTRY.read_text(encoding="utf-8"))
    runtime_scope = registry.get("runtime_scope", {})
    for enabled_flag in ["event_schema_enabled", "event_log_enabled", "realtime_api_enabled", "sse_enabled", "fallback_polling_enabled", "replay_api_enabled"]:
        if runtime_scope.get(enabled_flag) is not True:
            fail(f"{enabled_flag} must be true for Realtime API Gate")
    if runtime_scope.get("job_tracker_enabled") is not False:
        fail("job_tracker_enabled must remain false until JobTracker gate")

    security = registry.get("security", {})
    if security.get("token_in_url_allowed") is not False:
        fail("Realtime API must forbid tokens in URLs")
    if security.get("tenant_session_filter_server_side") is not True:
        fail("Realtime API must filter tenant/session server-side")
    if security.get("replay_cursor_validated") is not True:
        fail("Realtime API must validate replay cursors")

    routes = json.loads(ROUTE_MANIFEST.read_text(encoding="utf-8"))
    classified = {(route["path"], method) for route in routes.get("routes", []) for method in route.get("methods", [])}
    missing = REQUIRED_REALTIME_ROUTES - classified
    if missing:
        fail(f"Realtime routes missing route-security classification: {sorted(missing)}")

    runtime = {
        (route.path, method)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in (route.methods or set())
        if method not in {"HEAD", "OPTIONS"}
    }
    missing_runtime = REQUIRED_REALTIME_ROUTES - runtime
    if missing_runtime:
        fail(f"Realtime routes missing at runtime: {sorted(missing_runtime)}")

    route_gate_opened = "radi144_engine_api_runtime_route_gate_decision" in PROJECT_ANCHOR.read_text(encoding="utf-8")
    allowed_paths = ALLOWED_RADI144_RUNTIME_PATHS if route_gate_opened else set()
    forbidden_runtime_paths = sorted(
        path for path, _method in runtime for fragment in FORBIDDEN_PATH_FRAGMENTS if fragment in path and path not in allowed_paths
    )
    if forbidden_runtime_paths:
        fail(f"Job/engine/UI routes must remain blocked: {forbidden_runtime_paths}")

    if EventReplayResponse is None:
        fail("EventReplayResponse schema is not importable")

    print("[OK] realtime SSE and fallback replay routes are classified and present")
    print("[OK] realtime security flags enforce no URL tokens and validated replay cursors")
    print("[OK] job tracker, engine execution, results, and workflow UI routes remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
