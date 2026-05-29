"""Radi144 Engine Execution Gate Decision tests."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
EXECUTION_SCHEMA = ROOT / "packages" / "contracts" / "execution" / "radi144-engine-execution-decision.schema.v1.json"
EXECUTION_INSTANCE = ROOT / "packages" / "contracts" / "execution" / "radi144-engine-execution-decision.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_ENGINE_EXECUTION_GATE_DECISION.md"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"


def test_execution_decision_records_deferred_state() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scope = manifest["runtime_scope"]
    boundary = manifest["engine_execution_boundary"]

    assert scope["engine_execution_decision_recorded"] is True
    assert scope["engine_execution_enabled"] is False
    assert scope["cpu_execution_enabled"] is True
    assert scope["cpu_safe_execution_service_enabled"] is True
    assert scope["gpu_cuda_execution_enabled"] is False
    assert boundary["decision"] == "defer_execution_until_cpu_safe_gate"
    assert boundary["required_future_gate"] == "radi144_engine_execution_cpu_safe_gate_decision"


def test_execution_decision_contract_matches_instance() -> None:
    schema = json.loads(EXECUTION_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(EXECUTION_INSTANCE.read_text(encoding="utf-8"))

    assert schema["properties"]["schema_id"]["const"] == instance["schema_id"]
    assert instance["engine_execution_enabled"] is False
    assert instance["cpu_execution_enabled"] is False
    assert instance["gpu_cuda_execution_enabled"] is False
    assert instance["worker_runtime_may_call_domain_service"] is False
    assert instance["worker_runtime_may_write_results"] is False


def test_worker_runtime_still_does_not_open_gpu_or_direct_domain_calls() -> None:
    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")

    assert "process_next_queued" in worker_text
    for forbidden in ["build_plan(", "torch.cuda", "cupy", "gpu_manager"]:
        assert forbidden not in worker_text


def test_project_anchor_and_doc_point_to_cpu_safe_future_gate() -> None:
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    assert "radi144_engine_execution_gate_decision:" in project_text
    assert "status: execution_deferred_cpu_safe_gate_required" in project_text
    assert "radi144_engine_execution_cpu_safe_gate_decision" in project_text
    for blocker in ["engine_execution", "gpu_cuda_execution", "worker_domain_service_call", "worker_result_write"]:
        assert f"- {blocker}" in project_text
    for token in ["Engine execution remains blocked", "CPU execution", "GPU/CUDA execution", "radi144_engine_execution_cpu_safe_gate_decision"]:
        assert token in decision_text
