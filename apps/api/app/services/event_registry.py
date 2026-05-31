"""Event registry validation and durable event writer.

This gate validates and records event envelopes only. It deliberately exposes no
Realtime API, replay cursor endpoint, polling route, or engine progress logic.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import EventRecord
from app.schemas.event import EventEnvelopeCreate

ROOT = Path(__file__).resolve().parents[4]
EVENT_REGISTRY_PATH = ROOT / "packages" / "contracts" / "events" / "event-registry.v1.json"

FORBIDDEN_PAYLOAD_KEYS = {
    "raw_debug",
    "debug_json",
    "internal_state",
    "secret",
    "token",
    "access_token",
    "password",
}

CLIENT_HIDDEN_PAYLOAD_KEYS = {
    "compute_backend",
    "module_run_id",
    "gpu_cuda_execution_enabled",
    "cpu_execution_enabled",
    "worker_outcome",
    "projection_written",
}


class EventSchemaError(Exception):
    """Raised when an event envelope violates the committed event contract."""

    public_detail = "Invalid event envelope"

    def __init__(self, reason: str) -> None:
        super().__init__(self.public_detail)
        self.reason = reason


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, Any]:
    return json.loads(EVENT_REGISTRY_PATH.read_text(encoding="utf-8"))


def _contains_forbidden_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_PAYLOAD_KEYS:
                return key
            found = _contains_forbidden_key(nested)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _contains_forbidden_key(nested)
            if found is not None:
                return found
    return None


def project_payload_for_role(payload: dict[str, Any], role: str) -> dict[str, Any]:
    if role == "client":
        return {k: v for k, v in payload.items() if k not in CLIENT_HIDDEN_PAYLOAD_KEYS}
    return payload


class EventRegistryService:
    """Validate event envelopes against packages/contracts/events."""

    def __init__(self, registry: dict[str, Any] | None = None) -> None:
        self.registry = registry if registry is not None else _load_registry()

    @property
    def allowed_event_types(self) -> set[str]:
        allowed: set[str] = set()
        for family in self.registry.get("families", []):
            allowed.update(str(event_type) for event_type in family.get("events", []))
        return allowed

    def validate_envelope(self, envelope: EventEnvelopeCreate) -> None:
        if envelope.event_type not in self.allowed_event_types:
            raise EventSchemaError("unknown_event_type")
        forbidden_key = _contains_forbidden_key(envelope.payload)
        if forbidden_key is not None:
            raise EventSchemaError(f"forbidden_payload_key:{forbidden_key}")
        if envelope.event_type.startswith(("workflow.", "step.", "substep.")) and envelope.session_id is None:
            raise EventSchemaError("session_id_required")
        if envelope.event_type.startswith(("step.", "substep.")) and envelope.workflow_run_id is None:
            raise EventSchemaError("workflow_run_id_required")
        if envelope.event_type.startswith("substep.") and envelope.workflow_step_run_id is None:
            raise EventSchemaError("workflow_step_run_id_required")


class EventWriter:
    """Append schema-valid events to the tenant-scoped event log."""

    def __init__(self, session: AsyncSession, registry: EventRegistryService | None = None) -> None:
        self.session = session
        self.registry = registry if registry is not None else EventRegistryService()

    async def append(self, envelope: EventEnvelopeCreate) -> EventRecord:
        self.registry.validate_envelope(envelope)
        record = EventRecord(
            tenant_id=envelope.tenant_id,
            event_id=envelope.event_id,
            event_type=envelope.event_type,
            occurred_at=envelope.occurred_at,
            correlation_id=envelope.correlation_id,
            session_id=envelope.session_id,
            workflow_run_id=envelope.workflow_run_id,
            workflow_step_run_id=envelope.workflow_step_run_id,
            resource_type=envelope.resource_type,
            resource_id=envelope.resource_id,
            payload_json=envelope.payload,
        )
        self.session.add(record)
        await self.session.flush()
        return record
