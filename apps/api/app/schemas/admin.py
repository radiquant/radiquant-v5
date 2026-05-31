"""Admin route response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    """Safe admin audit-log projection."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    action: str
    user_id: UUID | None
    tenant_id: UUID
    details: dict[str, Any] | None


class AdminStatsResponse(BaseModel):
    """Tenant-scoped admin dashboard counters."""

    model_config = ConfigDict(extra="forbid")

    total_sessions: int
    total_clients: int
    active_sessions_24h: int
