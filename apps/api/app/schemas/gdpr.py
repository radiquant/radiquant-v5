"""GDPR export, anonymization, and retention schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GdprExportResponse(BaseModel):
    """Tenant-scoped GDPR data export for one client."""

    model_config = ConfigDict(extra="forbid")

    client_id: UUID
    tenant_id: UUID
    exported_at: datetime
    profile: dict[str, Any]
    sessions: list[dict[str, Any]]
    events: list[dict[str, Any]]


class GdprDeleteResponse(BaseModel):
    """GDPR anonymization response without hard deletion."""

    model_config = ConfigDict(extra="forbid")

    client_id: UUID
    anonymized_at: datetime
    fields_anonymized: list[str] = Field(default_factory=list)


class GdprRetainResponse(BaseModel):
    """GDPR retention extension response."""

    model_config = ConfigDict(extra="forbid")

    client_id: UUID
    retained_until: datetime
    reason: str
