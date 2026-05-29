#!/usr/bin/env python3
"""Validate the Radi144 Worker Progress Event Gate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
EVENT_REGISTRY = ROOT / "packages" / "contracts" / "events" / "event-registry.v1.json"
PROGRESS_SCHEMA = ROOT / "packages" / "contracts" / "events" / "radi144-worker-progress-events.schema.v1.json"
PROGRESS_INSTANCE = ROOT / "packages" / "contracts" / "events" / "radi144-worker-progress-events.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_WORKER_PROGRESS_EVENT_GATE.md"
WORKER_RUNTIME = ROOT / "apps" / "api" / "app" / "services" / "radi144" / "worker_runtime.py"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    event_registry = json.loads(EVENT_REGISTRY.read_text(encoding="utf-8"))
    schema = json.loads(PROGRESS_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(PROGRESS_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("worker_progress_events_enabled") is not True:
        fail("Radi144 worker progress events must be enabled")
    for flag in ["gpu_cuda_execution_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 {flag} must remain false")

    boundary = manifest.get("worker_progress_event_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/events/radi144-worker-progress-events.v1.instance.json":
        fail("Radi144 manifest must link worker progress events")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 worker progress event schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 worker progress event boundary schema_id drift")
    if instance.get("worker_progress_events_enabled") is not True or instance.get("forbidden_payload_keys_enforced") is not True:
        fail("Radi144 worker progress event instance must enable safe events")
    event_types = {event for family in event_registry.get("families", []) for event in family.get("events", [])}
    missing = sorted(set(instance.get("required_event_types", [])) - event_types)
    if missing:
        fail(f"Radi144 worker progress events missing from registry: {missing}")
    for flag in ["api_triggered_execution_enabled", "external_queue_enabled", "gpu_cuda_execution_enabled"]:
        if instance.get(flag) is not False:
            fail(f"Radi144 worker progress event {flag} must remain false")

    worker_text = WORKER_RUNTIME.read_text(encoding="utf-8")
    for token in ["EventWriter", "EventEnvelopeCreate", "_append_worker_event", "job.running", "job.done", "job.failed", "module.radi144.completed", "module.radi144.failed"]:
        if token not in worker_text:
            fail(f"Radi144 worker runtime missing event token: {token}")
    for forbidden in ["raw_debug", "debug_json", "internal_state", "access_token", "password", "torch.cuda", "cupy", "gpu_manager", "commit()"]:
        if forbidden in worker_text:
            fail(f"Radi144 worker event path must not contain forbidden token: {forbidden}")

    for token in ["radi144_worker_progress_event_gate_decision", "status: worker_progress_events_enabled_no_api_trigger_no_external_queue", "radi144_jobtracker_event_binding_gate_decision"]:
        if token not in project_text:
            fail(f"Project anchor missing worker progress event token: {token}")
    blockers = ["gpu_cuda_execution", "api_triggered_execution", "external_queue_daemon"]
    if "radi144_jobtracker_event_binding_gate_decision" not in project_text:
        blockers.append("jobtracker_event_binding")
    for blocker in blockers:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["event-truth", "EventWriter", "GPU/CUDA remains blocked", "radi144_jobtracker_event_binding_gate_decision"]:
        if token not in decision_text:
            fail(f"Worker progress event doc missing token: {token}")

    print("[OK] Radi144 worker progress events are enabled and event-registry bound")
    print("[OK] API-triggered execution, external queue, and GPU/CUDA remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
