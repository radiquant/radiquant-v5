#!/usr/bin/env python3
"""Validate the Radi144 Domain Service Gate without enabling engine execution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402
from app.services.radi144 import Radi144DomainService, Radi144InputContext  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
ALLOWED_RADI144_RUNTIME_PATHS = {
    "/engines/radi144/jobs",
    "/engines/radi144/jobs/{job_id}",
    "/engines/radi144/jobs/{job_id}/result",
}
FORBIDDEN_PATH_FRAGMENTS = {"/engines", "/engine", "/modules", "/results", "/radi144"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("engine_domain_service_enabled") is not True:
        fail("Radi144 domain service flag must be enabled")
    for blocked_flag in ["engine_execution_enabled", "engine_api_enabled", "result_persistence_enabled", "client_projection_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    service = Radi144DomainService()
    plan = service.build_plan(
        Radi144InputContext(
            tenant_id="tenant-a",
            client_id="client-a",
            session_id="session-a",
            goal_title="Ruhige Fokussierung",
            goal_description="Sanfter Wellbeing-Kontext",
            client_display_name="Klient A",
        )
    )
    if len(plan.client_vector) != 256:
        fail("Radi144 client vector must have 256 dimensions")
    if len(plan.normalized_matrix) != 12 or any(len(row) != 12 for row in plan.normalized_matrix):
        fail("Radi144 normalized matrix must be 12x12")
    if plan.synergy_seed.get("matrix_shape") != [12, 12]:
        fail("Radi144 synergy seed must retain matrix shape only, not raw matrix")

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    allowed_paths = ALLOWED_RADI144_RUNTIME_PATHS if runtime_scope.get("engine_api_runtime_routes_enabled") is True else set()
    forbidden = sorted(path for path in runtime_paths for fragment in FORBIDDEN_PATH_FRAGMENTS if fragment in path and path not in allowed_paths)
    if forbidden:
        fail(f"Radi144 engine/API/result routes must remain blocked: {forbidden}")

    print("[OK] Radi144 pure domain service builds deterministic 256-dim/12x12 plan")
    print("[OK] Radi144 engine API, workers, persistence, projections, and execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
