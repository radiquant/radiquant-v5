#!/usr/bin/env python3
"""Validate the Radi144 Projection Builder Gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.services.radi144.projection_builder import Radi144ProjectionBuilder  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
BUILDER_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-projection-builder.schema.v1.json"
BUILDER_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-projection-builder.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_PROJECTION_BUILDER_GATE.md"
SERVICE = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "projection_builder.py"
REQUIRED_BLOCKERS = {"worker_jobs", "engine_execution"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(BUILDER_SCHEMA.read_text(encoding="utf-8"))
    builder = json.loads(BUILDER_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("projection_builder_service_enabled") is not True:
        fail("Radi144 projection builder service flag must be enabled")
    for blocked_flag in ["worker_jobs_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(blocked_flag) is not False:
            fail(f"{blocked_flag} must remain false")

    boundary = manifest.get("projection_builder_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-projection-builder.v1.instance.json":
        fail("Radi144 manifest must link projection builder boundary")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != builder.get("schema_id"):
        fail("Radi144 projection builder schema_id drift")
    if builder.get("builder_service_enabled") is not True:
        fail("Projection builder service must be enabled")
    read_gate_opened = "radi144_api_projection_read_gate_decision" in project_text
    if builder.get("api_projection_reads_enabled") is not read_gate_opened:
        fail("Projection builder API read flag must match current read gate")
    for flag in ["worker_jobs_enabled", "engine_execution_enabled"]:
        if builder.get(flag) is not False:
            fail(f"Projection builder boundary must keep {flag} false")

    if not SERVICE.is_file() or Radi144ProjectionBuilder is None:
        fail("Projection builder service is not importable")
    service_text = SERVICE.read_text(encoding="utf-8")
    for token in ["Radi144ClientProjection", "Radi144TherapistProjection", "calm_summary", "professional_detail", "FORBIDDEN_PROJECTION_KEYS", "wellbeing_language_required"]:
        if token not in service_text:
            fail(f"Projection builder missing invariant token: {token}")
    if "raw_resonance_matrix" not in service_text or "client_vector" not in service_text:
        fail("Projection builder must explicitly forbid raw matrix/vector data")

    for token in ["radi144_projection_builder_gate_decision", "status: builder_service_enabled_not_wired_to_api_or_ui", "radi144_api_projection_read_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing projection builder token: {token}")
    for blocker in REQUIRED_BLOCKERS:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["service-only", "not wired to API", "worker jobs remain blocked", "engine execution remains blocked", "radi144_api_projection_read_gate_decision"]:
        if token not in decision_text:
            fail(f"Projection builder doc missing token: {token}")

    print("[OK] Radi144 projection builder service is enabled and contract-bound")
    print("[OK] Client and therapist projections exclude raw/debug/internal data")
    print("[OK] Workers and execution remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
