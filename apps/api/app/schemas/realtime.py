"""Realtime API Gate schemas.

These schemas expose safe event replay projections only. They contain no engine
results, job tracker runtime, or frontend progress state.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

EventReplayRole = Literal["client", "therapist", "admin"]


class EventReplayItem(BaseModel):
    """Safe tenant-scoped event projection for replay/fallback polling."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: str
    occurred_at: datetime
    tenant_id: UUID
    correlation_id: str
    session_id: UUID | None
    workflow_run_id: UUID | None
    workflow_step_run_id: UUID | None
    resource_type: str | None
    resource_id: str | None
    payload: dict[str, Any] = Field(default_factory=dict)


class EventReplayResponse(BaseModel):
    """Replay response with a validated cursor for fallback polling."""

    model_config = ConfigDict(extra="forbid")

    items: list[EventReplayItem]
    limit: int
    after_event_id: UUID | None
    next_cursor: UUID | None
    has_more: bool = False
    connection_state: Literal["fallback"] = "fallback"
