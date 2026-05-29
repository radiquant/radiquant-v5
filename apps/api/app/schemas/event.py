"""Event Schema Gate Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventEnvelopeCreate(BaseModel):
    """Schema-validated event envelope accepted by the event writer service."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(min_length=1, max_length=120)
    occurred_at: datetime
    tenant_id: UUID
    correlation_id: str = Field(min_length=1, max_length=120)
    session_id: UUID | None = None
    workflow_run_id: UUID | None = None
    workflow_step_run_id: UUID | None = None
    resource_type: str | None = Field(default=None, max_length=120)
    resource_id: str | None = Field(default=None, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


class EventRecordResponse(BaseModel):
    """Safe event projection for internal tests and future replay gate."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
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
    payload_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime
