"""HRV gate schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HRVReading(BaseModel):
    """Single HRV coherence reading for harmonization gating."""

    model_config = ConfigDict(extra="forbid")

    heart_rate_bpm: float
    coherence_score: float = Field(ge=0.0, le=1.0)
    measured_at: datetime
    source: Literal["webrtc", "manual", "simulated"]


class HRVGateResult(BaseModel):
    """Result of one HRV gate evaluation."""

    model_config = ConfigDict(extra="forbid")

    passed: bool
    coherence_score: float = Field(ge=0.0, le=1.0)
    threshold: float
    override_by_therapist: bool
