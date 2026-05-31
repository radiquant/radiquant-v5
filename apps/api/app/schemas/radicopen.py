"""RadiCopen API, result, and projection schemas."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RadiCopenRole = Literal["client", "therapist", "admin"]
RadiCopenJobStatus = Literal["queued", "storage_ready", "result_stored", "failed_closed"]
RadiCopenPotencyType = Literal["D", "C", "LM", "M", "F1", "F2", "F3"]


class RadiCopenRateData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    word: str
    normalized: str
    primary_sum: int = Field(ge=1)
    base_rate: int = Field(ge=1)
    fibonacci_pair: str
    fibonacci_rate: int = Field(ge=1)
    potency: str
    potency_bonus: int = Field(ge=0)
    final_rate: int = Field(ge=1)
    kozyrev_influence: float = Field(ge=0.95, le=1.05)


class RadiCopenLevelData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level_id: int = Field(ge=1, le=13)
    value: float = Field(ge=0, le=100)
    name: str
    description: str


class RadiCopenLevelResonance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    levels: list[RadiCopenLevelData] = Field(min_length=13, max_length=13)
    highest_level: int = Field(ge=1, le=13)
    highest_level_value: float = Field(ge=0, le=100)
    highest_level_name: str


class RadiCopenResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["radicopen_result_v1"] = "radicopen_result_v1"
    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    module_id: Literal["radicopen"] = "radicopen"
    algorithm_version: Literal["radicopen-v5-copen-v4"] = "radicopen-v5-copen-v4"
    manifest_version: str = Field(min_length=1, max_length=80)
    compute_backend: Literal["cpu"] = "cpu"
    hardware_entropy_enabled: Literal[False] = False
    entropy_source: Literal["os.urandom_stub"] = "os.urandom_stub"
    rate: RadiCopenRateData
    level_resonance: RadiCopenLevelResonance
    dominant_level: int = Field(ge=1, le=13)
    dominant_level_name: str
    level_distribution: dict[int, int] = Field(min_length=13, max_length=13)
    projection_status: Literal["pending_projection_builder"] = "pending_projection_builder"


class RadiCopenJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    workflow_run_id: UUID
    workflow_step_run_id: UUID
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)


class RadiCopenJobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: Literal["radicopen"] = "radicopen"
    tenant_id: UUID
    job_id: UUID | None = None
    session_id: UUID | None = None
    workflow_run_id: UUID | None = None
    workflow_step_run_id: UUID | None = None
    job_status: RadiCopenJobStatus | None = None
    route_status: Literal["job_record_created", "job_record_found"] = "job_record_found"
    message: str = Field(max_length=200)


class RadiCopenClientProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["client"] = "client"
    projection: Literal["copen_rate_summary"] = "copen_rate_summary"
    module_id: Literal["radicopen"] = "radicopen"
    summary_label: str
    final_rate: int = Field(ge=1)
    highest_level: int = Field(ge=1, le=13)
    highest_level_name: str
    raw_debug_excluded: Literal[True] = True


class RadiCopenTherapistProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["therapist"] = "therapist"
    projection: Literal["copen_rate_detail"] = "copen_rate_detail"
    module_id: Literal["radicopen"] = "radicopen"
    rate: RadiCopenRateData
    level_resonance: RadiCopenLevelResonance
    dominant_level: int = Field(ge=1, le=13)
    therapist_notes: list[str] = Field(min_length=1)
    raw_debug_excluded: Literal[True] = True


class RadiCopenAdminProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin"] = "admin"
    projection: Literal["operational_summary"] = "operational_summary"
    module_id: Literal["radicopen"] = "radicopen"
    job: dict[str, Any]
    execution: dict[str, Any]
    raw_debug_excluded: Literal[True] = True
