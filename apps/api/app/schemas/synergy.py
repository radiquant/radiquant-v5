"""Cross-module session synergy schemas."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SynergyConflict(BaseModel):
    """Conflict detected between two module result payloads."""

    model_config = ConfigDict(extra="forbid")

    module_a: str
    module_b: str
    conflict_type: str
    severity: Literal["low", "medium", "high"]


class SynergyResult(BaseModel):
    """Tenant-scoped cross-module synthesis for a session."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    tenant_id: UUID
    confidence: float = Field(ge=0, le=1)
    modules_complete: list[str]
    modules_pending: list[str]
    conflicts: list[SynergyConflict]
    consensus_summary: str
