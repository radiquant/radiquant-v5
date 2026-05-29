#!/usr/bin/env python3
"""Validate the Event Schema Gate event registry and durable event log."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.db.base import Base  # noqa: E402
from app import models  # noqa: F401,E402
from app.schemas.event import EventEnvelopeCreate  # noqa: E402
from app.services.event_registry import EventRegistryService, EventSchemaError  # noqa: E402

EVENT_REGISTRY = ROOT / "packages" / "contracts" / "events" / "event-registry.v1.json"
EVENT_ENVELOPE_SCHEMA = ROOT / "packages" / "contracts" / "events" / "event-envelope.schema.v1.json"
REQUIRED_EVENT_TYPES = {
    "workflow.created",
    "workflow.started",
    "workflow.phase.changed",
    "workflow.completed",
    "workflow.failed",
    "step.queued",
    "step.started",
    "step.progress",
    "step.completed",
    "step.failed",
    "substep.started",
    "substep.progress",
    "substep.output.ready",
    "substep.completed",
    "substep.failed",
    "job.queued",
    "job.running",
    "job.cancelled",
    "job.done",
    "job.failed",
}
def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    registry = json.loads(EVENT_REGISTRY.read_text(encoding="utf-8"))
    envelope_schema = json.loads(EVENT_ENVELOPE_SCHEMA.read_text(encoding="utf-8"))

    if registry.get("status") not in {"event_schema_gate_initialized", "realtime_api_gate_initialized"}:
        fail("Event registry status must reflect Event Schema Gate or a later compatible gate")
    runtime_scope = registry.get("runtime_scope", {})
    if runtime_scope.get("event_schema_enabled") is not True or runtime_scope.get("event_log_enabled") is not True:
        fail("Event schema and event log must be enabled")
    if runtime_scope.get("job_tracker_enabled") is not False:
        fail("job_tracker_enabled must remain false until JobTracker gate")

    if registry.get("envelope_schema") != "packages/contracts/events/event-envelope.schema.v1.json":
        fail("Event registry must point to the committed envelope schema")
    for field in registry.get("required_payload_fields", []):
        if field not in envelope_schema.get("required", []):
            fail(f"Required event field missing from envelope schema: {field}")

    service = EventRegistryService(registry=registry)
    missing_event_types = REQUIRED_EVENT_TYPES - service.allowed_event_types
    if missing_event_types:
        fail(f"Missing required event types: {sorted(missing_event_types)}")

    valid_envelope = EventEnvelopeCreate(
        event_type="workflow.created",
        tenant_id=uuid4(),
        session_id=uuid4(),
        occurred_at="2026-05-23T12:00:00Z",
        correlation_id="event-schema-gate",
        payload={"workflow_id": "W-A"},
    )
    service.validate_envelope(valid_envelope)

    try:
        service.validate_envelope(valid_envelope.model_copy(update={"event_type": "unknown.event"}))
    except EventSchemaError:
        pass
    else:
        fail("Unknown event type must be rejected")

    try:
        service.validate_envelope(valid_envelope.model_copy(update={"payload": {"raw_debug": "blocked"}}))
    except EventSchemaError:
        pass
    else:
        fail("Forbidden payload keys must be rejected")

    if "event_records" not in Base.metadata.tables:
        fail("event_records table missing from metadata")
    event_records = Base.metadata.tables["event_records"]
    for column in ["tenant_id", "event_id", "event_type", "occurred_at", "correlation_id", "payload_json"]:
        if column not in event_records.columns:
            fail(f"event_records missing column: {column}")

    security = registry.get("security", {})
    if security.get("token_in_url_allowed") is not False or security.get("event_payload_schema_validated") is not True:
        fail("Event registry security flags are incomplete")

    print(f"[OK] event registry event types validated: {len(service.allowed_event_types)}")
    print("[OK] event envelope schema validates required fields and payload safety")
    print("[OK] event_records table present; job tracker remains blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
