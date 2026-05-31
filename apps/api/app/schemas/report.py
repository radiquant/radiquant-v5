"""Client and therapist report schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.synergy import SynergyResult


class ClientReport(BaseModel):
    """Client-safe session report."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    tenant_id: UUID
    role: Literal["client", "therapist"]
    summary: str
    modules: list[str]
    generated_at: datetime


class TherapistAppendix(ClientReport):
    """Therapist report appendix with cross-module synthesis."""

    synergy: SynergyResult
