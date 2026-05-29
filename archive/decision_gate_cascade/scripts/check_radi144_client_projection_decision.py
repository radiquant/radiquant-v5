#!/usr/bin/env python3
"""Validate the Radi144 Client Projection Gate Decision.

This gate records role-specific projection boundaries. It does not build a
projection service, add UI, open result APIs, persist results, enqueue workers,
or execute Radi144.
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
RESULT_SCHEMA = ROOT / "packages" / "contracts" / "results" / "radi144-result.schema.v1.json"
PROJECTION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-client-projection.schema.v1.json"
PROJECTION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-client-projection.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_CLIENT_PROJECTION_GATE_DECISION.md"

FORBIDDEN_FIELDS = {
    "raw_resonance_matrix",
    "normalized_matrix",
    "client_vector",
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
}
ALLOWED_RADI144_RUNTIME_PATHS = {
    "/engines/radi144/jobs",
    "/engines/radi144/jobs/{job_id}",
    "/engines/radi144/jobs/{job_id}/result",
}
FORBIDDEN_RUNTIME_FRAGMENTS = {"/engines", "/engine", "/modules", "/results", "/radi144", "/jobs"}
REQUIRED_BLOCKERS = {
    "client_projection_builder",
    "result_persistence",
    "engine_api_runtime_routes",
    "worker_jobs",
    "engine_execution",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    projection_schema = json.loads(PROJECTION_SCHEMA.read_text(encoding="utf-8"))
    projection = json.loads(PROJECTION_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("client_projection_boundary_decided") is not True:
        fail("Radi144 client projection boundary decision flag must be set")
    for blocked_flag in ["client_projection_enabled", "result_persistence_enabled", "engine_api_enabled", "worker_jobs_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    boundary = manifest.get("client_projection_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-client-projection.v1.instance.json":
        fail("Radi144 manifest must link projection boundary instance")
    if projection_schema.get("properties", {}).get("schema_id", {}).get("const") != projection.get("schema_id"):
        fail("Radi144 projection schema_id drift")
    if projection.get("status") != "boundary_decided_builder_not_opened":
        fail("Radi144 projection boundary must remain builder-not-opened")
    if projection.get("builder_enabled") is not False or projection.get("runtime_api_enabled") is not False:
        fail("Radi144 projection builder/API must remain disabled")

    result_projection = result_schema.get("properties", {}).get("client_projection", {})
    if result_projection.get("properties", {}).get("status", {}).get("enum") != ["pending_projection_builder"]:
        fail("Radi144 result schema must keep projection placeholder pending")

    roles = projection.get("roles", {})
    if roles.get("client", {}).get("projection") != "calm_summary":
        fail("Client projection must be calm_summary")
    if roles.get("therapist", {}).get("projection") != "professional_detail":
        fail("Therapist projection must be professional_detail")

    forbidden = set(projection.get("forbidden_fields", []))
    if not FORBIDDEN_FIELDS.issubset(forbidden):
        fail(f"Projection forbidden fields incomplete: {sorted(FORBIDDEN_FIELDS - forbidden)}")
    payload_text = json.dumps(projection)
    if "medical" in payload_text.lower() and projection.get("language_policy", {}).get("medical_claims_allowed") is not False:
        fail("Projection boundary must forbid medical claims")
    if projection.get("language_policy", {}).get("wellbeing_language_only") is not True:
        fail("Projection boundary must require Wellbeing language")
    if projection.get("privacy_policy", {}).get("raw_debug_excluded") is not True:
        fail("Projection boundary must exclude raw debug")

    runtime_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    allowed_paths = ALLOWED_RADI144_RUNTIME_PATHS if "radi144_engine_api_runtime_route_gate_decision" in project_text else set()
    forbidden_runtime = sorted(path for path in runtime_paths for fragment in FORBIDDEN_RUNTIME_FRAGMENTS if fragment in path and path not in allowed_paths)
    if forbidden_runtime:
        fail(f"Projection decision must not open engine/result routes: {forbidden_runtime}")

    for token in ["radi144_client_projection_gate_decision", "status: boundary_decided_builder_not_opened", "radi144_result_persistence_storage_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing projection decision token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["boundary-only", "client sees no raw/debug/internal data", "projection builder remains closed", "radi144_result_persistence_storage_gate_decision"]:
        if token not in decision_text:
            fail(f"Decision doc missing token: {token}")

    print("[OK] Radi144 client projection boundary is decided without opening builder/runtime")
    print("[OK] Client and therapist role projections exclude raw/debug/internal data")
    print("[OK] Result persistence, API runtime routes, workers, and execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
