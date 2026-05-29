#!/usr/bin/env python3
"""Validate the Radi144 CPU-safe execution gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.services.radi144.cpu_safe_execution import Radi144CpuSafeExecutionInput, Radi144CpuSafeExecutionService  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
CPU_SCHEMA = ROOT / "packages" / "contracts" / "execution" / "radi144-engine-execution-cpu-safe.schema.v1.json"
CPU_INSTANCE = ROOT / "packages" / "contracts" / "execution" / "radi144-engine-execution-cpu-safe.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_ENGINE_EXECUTION_CPU_SAFE_GATE.md"
SERVICE = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "cpu_safe_execution.py"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(contains_key(nested, key) for nested in value.values())
    if isinstance(value, list):
        return any(contains_key(nested, key) for nested in value)
    return False


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(CPU_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(CPU_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("cpu_execution_enabled") is not True or runtime_scope.get("cpu_safe_execution_service_enabled") is not True:
        fail("Radi144 CPU-safe execution service must be enabled")
    if runtime_scope.get("engine_execution_enabled") is not False or runtime_scope.get("gpu_cuda_execution_enabled") is not False:
        fail("Radi144 general/GPU execution must remain disabled")

    boundary = manifest.get("cpu_safe_execution_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/execution/radi144-engine-execution-cpu-safe.v1.instance.json":
        fail("Radi144 manifest must link CPU-safe execution boundary")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 CPU-safe execution schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 CPU-safe execution boundary schema_id drift")
    if instance.get("compute_backend") != "cpu" or instance.get("cpu_safe_execution_service_enabled") is not True:
        fail("Radi144 CPU-safe execution instance must enable CPU service")
    for flag in ["worker_runtime_may_call_service", "worker_runtime_may_write_results", "gpu_cuda_execution_enabled"]:
        if instance.get(flag) is not False:
            fail(f"Radi144 CPU-safe execution must keep {flag} false")

    if not SERVICE.is_file() or Radi144CpuSafeExecutionService is None:
        fail("Radi144 CPU-safe execution service is not importable")
    service_text = SERVICE.read_text(encoding="utf-8")
    for token in ["Radi144CpuSafeExecutionService", "Radi144CpuSafeExecutionInput", "Radi144DomainService", "Radi144Result", "compute_backend=\"cpu\""]:
        if token not in service_text:
            fail(f"Radi144 CPU-safe service missing token: {token}")
    for forbidden in ["AsyncSession", "session.", "commit()", "Radi144ResultWriter", "Radi144ProjectionBuilder", "cuda"]:
        if forbidden in service_text:
            fail(f"Radi144 CPU-safe service must not own DB/write/project/GPU behavior: {forbidden}")

    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")
    wiring_gate_opened = "radi144_worker_cpu_execution_wiring_gate_decision" in project_text
    if not wiring_gate_opened and ("Radi144CpuSafeExecutionService" in worker_text or "Radi144DomainService" in worker_text):
        fail("Worker runtime must not be wired to CPU-safe execution yet")

    sample = Radi144CpuSafeExecutionService().execute(
        Radi144CpuSafeExecutionInput(
            module_run_id=uuid4(),
            tenant_id=uuid4(),
            client_id=uuid4(),
            session_id=uuid4(),
            workflow_run_id=uuid4(),
            goal_title="Calm focus",
            goal_description="Support a centered wellbeing session.",
        )
    )
    if sample.compute_backend != "cpu" or sample.provenance.compute_backend != "cpu":
        fail("Radi144 CPU-safe execution must return CPU result")
    payload = sample.model_dump(mode="json")
    for forbidden in ["raw_debug", "debug_json", "internal_state", "raw_resonance_matrix", "normalized_matrix", "client_vector"]:
        if contains_key(payload, forbidden):
            fail(f"Radi144 CPU-safe result leaked forbidden key: {forbidden}")

    for token in ["radi144_engine_execution_cpu_safe_gate_decision", "status: cpu_safe_execution_service_enabled_not_wired_to_worker", "radi144_worker_cpu_execution_wiring_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing CPU-safe execution token: {token}")
    blockers = ["gpu_cuda_execution"] if wiring_gate_opened else ["worker_cpu_execution_wiring", "worker_result_write", "gpu_cuda_execution"]
    for blocker in blockers:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["CPU-safe execution service", "not wired to worker", "GPU/CUDA remains blocked", "radi144_worker_cpu_execution_wiring_gate_decision"]:
        if token not in decision_text:
            fail(f"CPU-safe execution doc missing token: {token}")

    print("[OK] Radi144 CPU-safe execution service is enabled and contract-bound")
    print("[OK] GPU/CUDA remains blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
