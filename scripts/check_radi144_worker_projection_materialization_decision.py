#!/usr/bin/env python3
"""Validate the Radi144 Worker Projection Materialization Decision Gate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "projections" / "radi144-worker-projection-materialization-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "projections" / "radi144-worker-projection-materialization-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_WORKER_PROJECTION_MATERIALIZATION_DECISION_GATE.md"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
ROUTE_FILE = ROOT / "apps" / "api" / "app" / "routes" / "radi144.py"
ENGINE_MODEL = ROOT / "apps" / "api" / "app" / "models" / "engine.py"
ROUTE_MANIFEST = ROOT / "packages" / "contracts" / "routes" / "route-security-manifest.v1.json"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(DECISION_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(DECISION_INSTANCE.read_text(encoding="utf-8"))
    route_manifest = json.loads(ROUTE_MANIFEST.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("worker_projection_materialization_decision_recorded") is not True:
        fail("Radi144 worker projection materialization decision must be recorded")
    for flag in [
        "worker_projection_materialization_enabled",
        "materialized_projection_storage_enabled",
        "worker_projection_builder_enabled",
    ]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")
    if runtime_scope.get("api_projection_reads_enabled") is not True:
        fail("Radi144 API projection reads must remain enabled")

    boundary = manifest.get("worker_projection_materialization_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/projections/radi144-worker-projection-materialization-decision.v1.instance.json":
        fail("Radi144 manifest must link worker projection materialization decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 worker projection materialization schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 worker projection materialization boundary schema_id drift")
    if instance.get("decision") != "defer_worker_projection_materialization_until_storage_contract":
        fail("Radi144 worker projection materialization must be deferred")
    if instance.get("source_of_truth") != "module_results.result_payload_json":
        fail("Radi144 projection source of truth must remain stored result payload")
    if instance.get("required_future_gate") != "radi144_materialized_projection_storage_gate_decision":
        fail("Radi144 worker projection materialization must point to storage future gate")
    for flag in [
        "worker_projection_materialization_enabled",
        "materialized_projection_storage_enabled",
        "worker_projection_builder_enabled",
    ]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 worker projection materialization {flag} must remain false")

    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")
    for forbidden in ["Radi144ProjectionBuilder", "build_projection(", "projection_status =", "projection_payload", "ModuleProjection"]:
        if forbidden in worker_text:
            fail(f"Worker runtime must not materialize projections: {forbidden}")
    route_text = ROUTE_FILE.read_text(encoding="utf-8")
    for token in ["Radi144ProjectionBuilder", "result_payload_json", "role", "Radi144Result.model_validate"]:
        if token not in route_text:
            fail(f"API projection read route must remain on-demand: {token}")
    for forbidden in ["projection_payload", "ModuleProjection", "projection_cache"]:
        if forbidden in route_text:
            fail(f"API route must not use materialized projection storage: {forbidden}")
    model_text = ENGINE_MODEL.read_text(encoding="utf-8")
    for forbidden in ["ModuleProjection", "projection_payload_json", "projection_role", "materialized_projection"]:
        if forbidden in model_text:
            fail(f"Materialized projection storage must remain absent: {forbidden}")
    route_paths = {route.get("path") for route in route_manifest.get("routes", [])}
    for forbidden_path in ["/engines/radi144/jobs/{job_id}/projections", "/engines/radi144/jobs/{job_id}/projection-cache"]:
        if forbidden_path in route_paths:
            fail(f"Forbidden projection runtime route opened: {forbidden_path}")

    for token in [
        "radi144_worker_projection_materialization_decision_gate",
        "status: worker_projection_materialization_deferred_api_read_projection_only",
        "radi144_materialized_projection_storage_gate_decision",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing worker projection materialization token: {token}")
    for blocker in [
        "worker_projection_builder",
        "materialized_projection_storage",
        "projection_payload_write_in_worker",
        "raw_debug_projection_storage",
        "new_projection_runtime_route",
    ]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["conservative no-go", "API read projection remains on-demand", "radi144_materialized_projection_storage_gate_decision"]:
        if token not in decision_text:
            fail(f"Worker projection materialization doc missing token: {token}")

    print("[OK] Radi144 worker projection materialization decision is recorded conservatively")
    print("[OK] Projection reads remain on-demand; worker/materialized projection writes remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
