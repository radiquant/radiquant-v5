#!/usr/bin/env python3
"""Validate the Radi144 External Queue Decision Gate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
DECISION_SCHEMA = ROOT / "packages" / "contracts" / "jobs" / "radi144-external-queue-decision.schema.v1.json"
DECISION_INSTANCE = ROOT / "packages" / "contracts" / "jobs" / "radi144-external-queue-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_EXTERNAL_QUEUE_DECISION_GATE.md"
ROUTE_MANIFEST = ROOT / "packages" / "contracts" / "routes" / "route-security-manifest.v1.json"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_JSON = ROOT / "package.json"

FORBIDDEN_QUEUE_TOKENS = [
    "celery",
    "dramatiq",
    "arq",
    "rq.worker",
    "rq.queue",
    "apscheduler",
    "while True",
    "asyncio.create_task",
]


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
    if runtime_scope.get("external_queue_decision_recorded") is not True:
        fail("Radi144 external queue decision must be recorded")
    for flag in ["external_queue_enabled", "daemon_enabled", "gpu_cuda_execution_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 runtime_scope {flag} must remain false")

    boundary = manifest.get("external_queue_decision_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/jobs/radi144-external-queue-decision.v1.instance.json":
        fail("Radi144 manifest must link external queue decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 external queue decision schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 external queue decision boundary schema_id drift")
    if instance.get("decision") != "defer_external_queue_until_operations_worker_gate":
        fail("Radi144 external queue must be deferred")
    if instance.get("allowed_worker_invocation") != "internal_service_call_only":
        fail("Radi144 worker invocation must remain internal service only")
    if instance.get("required_future_gate") != "radi144_operations_worker_gate_decision":
        fail("Radi144 external queue decision must point to operations worker future gate")
    for flag in ["external_queue_enabled", "daemon_enabled", "api_triggered_execution_enabled", "gpu_cuda_execution_enabled"]:
        if instance.get(flag) is not False or boundary.get(flag) is not False:
            fail(f"Radi144 external queue decision {flag} must remain false")

    route_paths = {route.get("path") for route in route_manifest.get("routes", [])}
    for forbidden_path in ["/workers", "/engines/radi144/worker", "/engines/radi144/jobs/{job_id}/run"]:
        if forbidden_path in route_paths:
            fail(f"Forbidden worker control route opened: {forbidden_path}")

    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")
    dependency_text = f"{PYPROJECT.read_text(encoding='utf-8')}\n{PACKAGE_JSON.read_text(encoding='utf-8')}"
    worker_scan = worker_text.lower()
    dependency_scan = dependency_text.lower()
    for token in FORBIDDEN_QUEUE_TOKENS:
        token_scan = token.lower()
        if token_scan in worker_scan or token_scan in dependency_scan:
            fail(f"External queue/daemon token must remain absent: {token}")
    for required in ["process_next_queued", "caller owns transaction", "must not commit", "use external queues"]:
        if required not in worker_text:
            fail(f"Worker runtime must document internal-only boundary: {required}")

    for token in [
        "radi144_external_queue_decision_gate",
        "status: external_queue_deferred_internal_worker_only",
        "radi144_worker_projection_materialization_decision_gate",
    ]:
        if token not in project_text:
            fail(f"Project anchor missing external queue decision token: {token}")
    for blocker in ["external_queue_daemon", "api_triggered_execution", "gpu_cuda_execution", "public_worker_control_api"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["conservative no-go", "No new runtime route", "radi144_operations_worker_gate_decision"]:
        if token not in decision_text:
            fail(f"External queue decision doc missing token: {token}")

    print("[OK] Radi144 external queue decision is recorded conservatively")
    print("[OK] External daemon, public worker API, API-triggered execution, and GPU/CUDA remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
