"""LLM therapist copilot schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CopilotRequest(BaseModel):
    """Therapist-only copilot request."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    question: str = Field(max_length=500)
    role: Literal["therapist"]


class CopilotResponse(BaseModel):
    """Simulated copilot response after safety checks."""

    model_config = ConfigDict(extra="forbid")

    answer: str
    pii_redacted: bool
    claim_violations: list[str]
    model_used: str
    generated_at: datetime
