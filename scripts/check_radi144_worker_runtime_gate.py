#!/usr/bin/env python3
"""Validate the Radi144 Worker Runtime Gate Decision."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.services.radi144.worker_runtime import Radi144WorkerRuntimeService  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
RUNTIME_SCHEMA = ROOT / "packages" / "contracts" / "jobs" / "radi144-worker-runtime.schema.v1.json"
RUNTIME_INSTANCE = ROOT / "packages" / "contracts" / "jobs" / "radi144-worker-runtime.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_WORKER_RUNTIME_GATE_DECISION.md"
SERVICE = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(RUNTIME_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("worker_runtime_enabled") is not True or runtime_scope.get("worker_runtime_service_enabled") is not True:
        fail("Radi144 worker runtime service must be enabled")
    if runtime_scope.get("engine_execution_enabled") is not False:
        fail("Radi144 engine execution must remain disabled")

    boundary = manifest.get("worker_runtime_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/jobs/radi144-worker-runtime.v1.instance.json":
        fail("Radi144 manifest must link worker runtime boundary")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 worker runtime schema_id drift")
    if instance.get("worker_runtime_service_enabled") is not True:
        fail("Radi144 worker runtime service must be enabled")
    for flag in ["engine_execution_enabled", "result_writer_enabled_in_worker", "projection_builder_enabled_in_worker", "external_queue_enabled"]:
        if instance.get(flag) is not False:
            fail(f"Radi144 worker runtime must keep {flag} false")
    if instance.get("fail_closed_status") != "failed_closed":
        fail("Radi144 worker runtime must fail closed")

    if not SERVICE.is_file() or Radi144WorkerRuntimeService is None:
        fail("Radi144 worker runtime service is not importable")
    service_text = SERVICE.read_text(encoding="utf-8")
    wiring_gate_opened = "radi144_worker_cpu_execution_wiring_gate_decision" in project_text
    required_tokens = ["Radi144WorkerRuntimeService", "process_next_queued", "failed_closed", "await self.session.flush()"]
    if not wiring_gate_opened:
        required_tokens.append("engine_execution_gate_closed")
    for token in required_tokens:
        if token not in service_text:
            fail(f"Radi144 worker runtime missing token: {token}")
    forbidden_tokens = ["Radi144ProjectionBuilder", "torch.cuda", "cupy", "gpu_manager", "commit()"]
    if not wiring_gate_opened:
        forbidden_tokens.extend(["Radi144DomainService", "Radi144ResultWriter"])
    for forbidden in forbidden_tokens:
        if forbidden in service_text:
            fail(f"Radi144 worker runtime must not execute/write/project/commit: {forbidden}")

    for token in ["radi144_worker_runtime_gate_decision", "status: worker_runtime_service_enabled_fail_closed_no_engine_execution", "radi144_engine_execution_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing worker runtime token: {token}")
    blockers = ["engine_execution", "projection_builder_in_worker"] if wiring_gate_opened else ["engine_execution", "result_writer_in_worker", "projection_builder_in_worker"]
    for blocker in blockers:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["fail-closed", "engine execution remains blocked", "does not write results", "radi144_engine_execution_gate_decision"]:
        if token not in decision_text:
            fail(f"Worker runtime doc missing token: {token}")

    print("[OK] Radi144 worker runtime service is enabled fail-closed")
    print("[OK] Engine execution, projections, and external queues remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
