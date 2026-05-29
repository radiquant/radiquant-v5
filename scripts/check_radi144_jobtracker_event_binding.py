#!/usr/bin/env python3
"""Validate Radi144 JobTracker Event Binding Gate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "contracts" / "engines" / "radi144.engine-manifest.v1.json"
BINDING_SCHEMA = ROOT / "packages" / "contracts" / "events" / "radi144-jobtracker-event-binding.schema.v1.json"
BINDING_INSTANCE = ROOT / "packages" / "contracts" / "events" / "radi144-jobtracker-event-binding.v1.instance.json"
PROJECT_ANCHOR = ROOT / "docs" / "pi" / "project.yml"
DECISION_DOC = ROOT / "docs" / "architecture" / "RADI144_JOBTRACKER_EVENT_BINDING_GATE.md"
JOBTRACKER = ROOT / "apps" / "web-astro" / "src" / "components" / "JobTrackerStatusIsland.tsx"
API_CLIENT = ROOT / "apps" / "web-astro" / "src" / "lib" / "api" / "client.ts"
API_TYPES = ROOT / "apps" / "web-astro" / "src" / "lib" / "api" / "types.ts"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    schema = json.loads(BINDING_SCHEMA.read_text(encoding="utf-8"))
    instance = json.loads(BINDING_INSTANCE.read_text(encoding="utf-8"))
    project_text = PROJECT_ANCHOR.read_text(encoding="utf-8")
    decision_text = DECISION_DOC.read_text(encoding="utf-8")

    runtime_scope = manifest.get("runtime_scope", {})
    if runtime_scope.get("jobtracker_event_binding_enabled") is not True:
        fail("Radi144 JobTracker event binding must be enabled")
    for flag in ["gpu_cuda_execution_enabled", "engine_execution_enabled"]:
        if runtime_scope.get(flag) is not False:
            fail(f"Radi144 {flag} must remain false")

    boundary = manifest.get("jobtracker_event_binding_boundary", {})
    if boundary.get("instance_path") != "packages/contracts/events/radi144-jobtracker-event-binding.v1.instance.json":
        fail("Radi144 manifest must link JobTracker binding")
    if schema.get("properties", {}).get("schema_id", {}).get("const") != instance.get("schema_id"):
        fail("Radi144 JobTracker binding schema_id drift")
    if boundary.get("schema_id") != instance.get("schema_id"):
        fail("Radi144 JobTracker binding boundary schema_id drift")
    if instance.get("jobtracker_event_binding_enabled") is not True or instance.get("source_of_truth") != "event_records":
        fail("Radi144 JobTracker must bind to event_records")
    for flag in ["api_triggered_execution_enabled", "external_queue_enabled", "gpu_cuda_execution_enabled"]:
        if instance.get(flag) is not False:
            fail(f"Radi144 JobTracker binding {flag} must remain false")

    jobtracker_text = JOBTRACKER.read_text(encoding="utf-8")
    types_text = API_TYPES.read_text(encoding="utf-8")
    client_text = API_CLIENT.read_text(encoding="utf-8")
    for token in ["Radi144WorkerEventType", "RADI144_WORKER_EVENT_TYPES", "isRadi144WorkerEvent", "Radi144 Worker-Status", "Radi144 Event-Truth", "listSessionEvents"]:
        if token not in jobtracker_text:
            fail(f"JobTracker missing binding token: {token}")
    for event_type in instance.get("event_types", []):
        if event_type not in jobtracker_text or event_type not in types_text:
            fail(f"JobTracker/type contract missing event type: {event_type}")
    if "fetch(" in jobtracker_text or "EventSource" in jobtracker_text:
        fail("JobTracker must use central API replay only")
    if "/sessions/{session_id}/events" not in client_text:
        fail("Central API client must expose classified session events route")
    for forbidden in ["raw_debug", "debug_json", "internal_state", "/engines", "gpu", "cuda"]:
        if forbidden in jobtracker_text:
            fail(f"JobTracker must not expose forbidden/opened-later token: {forbidden}")

    for token in ["radi144_jobtracker_event_binding_gate_decision", "status: jobtracker_bound_to_event_truth_no_execution_trigger", "radi144_external_queue_decision_gate"]:
        if token not in project_text:
            fail(f"Project anchor missing JobTracker binding token: {token}")
    for blocker in ["gpu_cuda_execution", "api_triggered_execution", "external_queue_daemon"]:
        if f"- {blocker}" not in project_text:
            fail(f"Project anchor must keep blocker: {blocker}")
    for token in ["Event-truth only", "No synthetic progress", "radi144_external_queue_decision_gate"]:
        if token not in decision_text:
            fail(f"JobTracker binding doc missing token: {token}")

    print("[OK] Radi144 JobTracker is bound to event truth via classified replay")
    print("[OK] No API-triggered execution, external queue, or GPU/CUDA binding opened")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
