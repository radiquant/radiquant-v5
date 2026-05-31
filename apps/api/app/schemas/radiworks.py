"""RadiWorks API, result, and projection schemas."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RadiWorksRole = Literal["client", "therapist", "admin"]
RadiWorksJobStatus = Literal["queued", "storage_ready", "result_stored", "failed_closed"]


class RadiWorksRateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    value: str | None = Field(default=None, max_length=160)
    url: str | None = Field(default=None, max_length=300)


class RadiWorksRateScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    score: int = Field(ge=0)
    normalized_score: float = Field(ge=0, le=1)
    level: int = Field(ge=1, le=12)
    potency: str
    rate: str | None = None
    url: str | None = None


class RadiWorksMonteCarloSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trials: int = Field(ge=1)
    mean_score: float = Field(ge=0, le=1)
    max_score: float = Field(ge=0, le=1)
    stability: float = Field(ge=0, le=1)


class RadiWorksResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["radiworks_result_v1"] = "radiworks_result_v1"
    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    module_id: Literal["radiworks"] = "radiworks"
    algorithm_version: Literal["radiworks-v5-os-entropy-v1"] = "radiworks-v5-os-entropy-v1"
    manifest_version: str = Field(min_length=1, max_length=80)
    compute_backend: Literal["cpu"] = "cpu"
    hardware_entropy_enabled: Literal[False] = False
    entropy_source: Literal["os.urandom_stub"] = "os.urandom_stub"
    rates: list[RadiWorksRateScore] = Field(min_length=1, max_length=105)
    general_vitality: int = Field(ge=0, le=10000)
    monte_carlo: RadiWorksMonteCarloSummary
    trials: int = Field(ge=1)
    top_rate_names: list[str] = Field(min_length=1, max_length=10)
    projection_status: Literal["pending_projection_builder"] = "pending_projection_builder"


class RadiWorksJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    workflow_run_id: UUID
    workflow_step_run_id: UUID
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)


class RadiWorksJobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: Literal["radiworks"] = "radiworks"
    tenant_id: UUID
    job_id: UUID | None = None
    session_id: UUID | None = None
    workflow_run_id: UUID | None = None
    workflow_step_run_id: UUID | None = None
    job_status: RadiWorksJobStatus | None = None
    route_status: Literal["job_record_created", "job_record_found"] = "job_record_found"
    message: str = Field(max_length=200)


class RadiWorksClientProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["client"] = "client"
    projection: Literal["rate_summary"] = "rate_summary"
    module_id: Literal["radiworks"] = "radiworks"
    summary_label: str
    vitality_band: Literal["low", "steady", "high"]
    top_rates: list[RadiWorksRateScore] = Field(min_length=1, max_length=3)
    raw_debug_excluded: Literal[True] = True


class RadiWorksTherapistProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["therapist"] = "therapist"
    projection: Literal["rate_analysis_detail"] = "rate_analysis_detail"
    module_id: Literal["radiworks"] = "radiworks"
    rates: list[RadiWorksRateScore] = Field(min_length=1, max_length=20)
    general_vitality: int
    monte_carlo: RadiWorksMonteCarloSummary
    therapist_notes: list[str] = Field(min_length=1)
    raw_debug_excluded: Literal[True] = True


class RadiWorksAdminProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin"] = "admin"
    projection: Literal["operational_summary"] = "operational_summary"
    module_id: Literal["radiworks"] = "radiworks"
    job: dict[str, Any]
    execution: dict[str, Any]
    raw_debug_excluded: Literal[True] = True
