"""Harmonization plan request and response schemas."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HarmonizationPlanCreate(BaseModel):
    """Create a draft harmonization plan for explicit approval."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    plan_payload_json: dict[str, Any] = Field(default_factory=dict)


class HarmonizationPlanResponse(BaseModel):
    """Tenant-scoped harmonization plan projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    session_id: UUID
    tenant_id: UUID
    status: str
    plan_payload_json: dict[str, Any]
    created_by_user_id: UUID
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    created_at: datetime


class HarmonizationPlanListResponse(BaseModel):
    """List response for tenant-scoped harmonization plans."""

    model_config = ConfigDict(extra="forbid")

    items: list[HarmonizationPlanResponse]

class JobStatusEnum(str, enum.Enum):
    """Harmonization job lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HarmonizationJobResponse(BaseModel):
    """Tenant-scoped harmonization job projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    plan_id: UUID
    tenant_id: UUID
    status: JobStatusEnum
    hardware_ack: bool
    started_at: datetime | None
    paused_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
