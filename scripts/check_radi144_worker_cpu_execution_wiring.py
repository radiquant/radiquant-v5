#!/usr/bin/env python3
"""Validate the Radi144 Worker CPU Execution Wiring Gate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
WIRING_SCHEMA = ROOT / "packages" / "contracts" / "execution" / "radi144-worker-cpu-execution-wiring.schema.v1.json"
WIRING_INSTANCE = ROOT / "packages" / "contracts" / "execution" / "radi144-worker-cpu-execution-wiring.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_WORKER_CPU_EXECUTION_WIRING_GATE.md"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"
RESULT_WRITER = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "result_writer.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(WIRING_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(WIRING_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    for flag in ["worker_cpu_execution_wiring_enabled", "worker_result_write_enabled", "cpu_execution_enabled"]:
        if runtime_scope.get(flag) is not True:
            fail(f"Radi144 {flag} must be enabled")
    for flag in ["gpu_cuda_execution_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 {flag} must remain false")

    boundary = manifest.get("worker_cpu_execution_wiring_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/execution/radi144-worker-cpu-execution-wiring.v1.instance.json":
        fail("Radi144 manifest must link worker CPU execution wiring boundary")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 worker CPU wiring schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 worker CPU wiring boundary schema_id drift")
    for flag in ["worker_cpu_execution_wiring_enabled", "worker_runtime_may_call_cpu_service", "worker_runtime_may_write_results", "consent_gate_required"]:
        if instance.get(flag) is not True:
            fail(f"Radi144 worker CPU wiring {flag} must be true")
    for flag in ["gpu_cuda_execution_enabled", "api_triggered_execution_enabled", "external_queue_enabled"]:
        if instance.get(flag) is not False:
            fail(f"Radi144 worker CPU wiring {flag} must remain false")
    if instance.get("compute_backend") != "cpu":
        fail("Radi144 worker CPU wiring backend must be cpu")

    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")
    for token in ["Radi144CpuSafeExecutionService", "Radi144ResultWriter", "ConsentService", "assert_analysis_allowed", "process_next_queued", "result_stored_cpu_safe"]:
        if token not in worker_text:
            fail(f"Radi144 worker runtime missing wiring token: {token}")
    for forbidden in ["torch.cuda", "cupy", "gpu_manager", "Radi144ProjectionBuilder", "commit()"]:
        if forbidden in worker_text:
            fail(f"Radi144 worker runtime must not open forbidden behavior: {forbidden}")

    writer_text = RESULT_WRITER.read_text(encoding="utf-8")
    for token in ["existing.status != \"queued\"", "result_exists", "status=\"result_stored\""]:
        if token not in writer_text:
            fail(f"Radi144 result writer missing queued ModuleRun support token: {token}")
    if "await self.session.commit" in writer_text or ".commit()" in writer_text:
        fail("Radi144 result writer must not commit transactions")

    for token in ["radi144_worker_cpu_execution_wiring_gate_decision", "status: worker_cpu_execution_and_result_write_enabled_no_gpu_no_api_trigger", "radi144_worker_progress_event_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing worker CPU wiring token: {token}")
    for blocker in ["gpu_cuda_execution", "api_triggered_execution", "external_queue_daemon", "worker_projection_builder"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["Worker runtime may call", "active analysis consent", "GPU/CUDA", "radi144_worker_progress_event_gate_decision"]:
        if token not in decision_text:
            fail(f"Worker CPU wiring doc missing token: {token}")

    print("[OK] Radi144 worker CPU execution wiring is enabled")
    print("[OK] Consent, tenant joins, result writer, and no GPU/API-trigger invariants validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
