"""Session domain request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.session import SessionStatus


class SessionGoalCreate(BaseModel):
    """Goal/intention for a minimal client session."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class SessionCreateRequest(BaseModel):
    """Start a minimal consent-gated session for a client."""

    model_config = ConfigDict(extra="forbid")

    client_id: UUID
    goal: SessionGoalCreate


class SessionStatusUpdateRequest(BaseModel):
    """Close an active session with a terminal status."""

    model_config = ConfigDict(extra="forbid")

    status: SessionStatus


class SessionGoalResponse(BaseModel):
    """Safe session goal projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: UUID
    title: str
    description: str
    created_at: datetime
    updated_at: datetime


class SessionResponse(BaseModel):
    """Safe session projection without workflow, realtime, or engine fields."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: UUID
    goal_id: UUID
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    goal: SessionGoalResponse


class SessionListResponse(BaseModel):
    """List response for tenant-scoped sessions."""

    model_config = ConfigDict(extra="forbid")

    items: list[SessionResponse]
    limit: int
    offset: int
