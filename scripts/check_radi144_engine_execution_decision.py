#!/usr/bin/env python3
"""Validate the conservative Radi144 Engine Execution Gate Decision."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
EXECUTION_SCHEMA = ROOT / "packages" / "contracts" / "execution" / "radi144-engine-execution-decision.schema.v1.json"
EXECUTION_INSTANCE = ROOT / "packages" / "contracts" / "execution" / "radi144-engine-execution-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_ENGINE_EXECUTION_GATE_DECISION.md"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(EXECUTION_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(EXECUTION_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("engine_execution_decision_recorded") is not True:
        fail("Radi144 engine execution decision must be recorded")
    if runtime_scope.get("engine_execution_enabled") is not False:
        fail("Radi144 engine_execution_enabled must remain false")
    cpu_safe_gate_opened = "radi144_engine_execution_cpu_safe_gate_decision" in project_text
    if runtime_scope.get("cpu_execution_enabled") is not cpu_safe_gate_opened:
        fail("Radi144 cpu_execution_enabled must match CPU-safe gate state")
    if runtime_scope.get("gpu_cuda_execution_enabled") is not False:
        fail("Radi144 gpu_cuda_execution_enabled must remain false")

    boundary = manifest.get("engine_execution_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/execution/radi144-engine-execution-decision.v1.instance.json":
        fail("Radi144 manifest must link engine execution decision")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 engine execution schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 engine execution boundary schema_id drift")
    if instance.get("decision") != "defer_execution_until_cpu_safe_gate":
        fail("Radi144 engine execution decision must be deferred")
    for flag in ["engine_execution_enabled", "cpu_execution_enabled", "gpu_cuda_execution_enabled", "worker_runtime_may_call_domain_service", "worker_runtime_may_write_results"]:
        if instance.get(flag) is not False:
            fail(f"Radi144 execution decision must keep {flag} false")
    if instance.get("required_future_gate") != "radi144_engine_execution_cpu_safe_gate_decision":
        fail("Radi144 execution decision must point to CPU-safe future gate")

    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")
    wiring_gate_opened = "radi144_worker_cpu_execution_wiring_gate_decision" in project_text
    forbidden_tokens = ["build_plan(", "torch.cuda", "cupy", "gpu_manager"]
    if not wiring_gate_opened:
        forbidden_tokens.extend(["Radi144DomainService", "Radi144ResultWriter", "persist_result("])
    for forbidden in forbidden_tokens:
        if forbidden in worker_text:
            fail(f"Worker runtime must not open forbidden execution/write behavior: {forbidden}")
    required_tokens = [] if wiring_gate_opened else ["failed_closed", "engine_execution_gate_closed"]
    for required in required_tokens:
        if required not in worker_text:
            fail(f"Worker runtime must remain fail-closed: {required}")

    for token in ["radi144_engine_execution_gate_decision", "status: execution_deferred_cpu_safe_gate_required", "radi144_engine_execution_cpu_safe_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing execution decision token: {token}")
    required_blockers = ["engine_execution", "gpu_cuda_execution", "worker_domain_service_call", "worker_result_write"]
    if not cpu_safe_gate_opened:
        required_blockers.append("cpu_execution")
    for blocker in required_blockers:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["Engine execution remains blocked", "CPU execution", "GPU/CUDA execution", "radi144_engine_execution_cpu_safe_gate_decision"]:
        if token not in decision_text:
            fail(f"Execution decision doc missing token: {token}")

    print("[OK] Radi144 engine execution decision is recorded conservatively")
    print("[OK] Worker execution, GPU/CUDA execution, and worker result writes remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
