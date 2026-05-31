"""Retention policy and cleanup schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RetentionPolicyResponse(BaseModel):
    """Tenant-scoped retention policy projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    data_type: str
    retention_days: int = Field(ge=1)
    enabled: bool
    created_at: datetime


class RetentionCleanupReport(BaseModel):
    """Summary of one retention cleanup run."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    data_type: str
    records_processed: int
    records_anonymized: int
    ran_at: datetime
