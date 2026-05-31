"""RadiMorphic API, result, and projection schemas."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RadiMorphicRole = Literal["client", "therapist", "admin"]
RadiMorphicJobStatus = Literal["queued", "storage_ready", "result_stored", "failed_closed"]


class RadiMorphicNlsProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    frequency_hz: float = Field(ge=0)
    rates: list[float] = Field(default_factory=list, max_length=24)
    description: str | None = Field(default=None, max_length=300)


class RadiMorphicMultiplexScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_index: int = Field(ge=0)
    resonance_score: float = Field(ge=0, le=1)
    raw_score: float = Field(ge=0)


class RadiMorphicResonance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    name: str
    category: str
    frequency_hz: float
    resonance_score: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)


class RadiMorphicScanMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quality_score: float = Field(ge=0, le=1)
    morphic_field: float = Field(ge=0, le=1)
    holographic_entropy: float = Field(ge=0, le=1)


class RadiMorphicResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["radimorphic_result_v1"] = "radimorphic_result_v1"
    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    module_id: Literal["radimorphic"] = "radimorphic"
    algorithm_version: Literal["radimorphic-v5-hadamard-v1"] = "radimorphic-v5-hadamard-v1"
    manifest_version: str = Field(min_length=1, max_length=80)
    compute_backend: Literal["cpu"] = "cpu"
    gpu_cuda_execution_enabled: Literal[False] = False
    hardware_entropy_enabled: Literal[False] = False
    entropy_source: Literal["os.urandom_stub"] = "os.urandom_stub"
    matrix_shape: tuple[int, int]
    top_resonances: list[RadiMorphicResonance] = Field(min_length=1, max_length=20)
    metrics: RadiMorphicScanMetrics
    total_profiles: int = Field(ge=1)
    projection_status: Literal["pending_projection_builder"] = "pending_projection_builder"


class RadiMorphicJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    workflow_run_id: UUID
    workflow_step_run_id: UUID
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)


class RadiMorphicJobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: Literal["radimorphic"] = "radimorphic"
    tenant_id: UUID
    job_id: UUID | None = None
    session_id: UUID | None = None
    workflow_run_id: UUID | None = None
    workflow_step_run_id: UUID | None = None
    job_status: RadiMorphicJobStatus | None = None
    route_status: Literal["job_record_created", "job_record_found"] = "job_record_found"
    message: str = Field(max_length=200)


class RadiMorphicClientProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["client"] = "client"
    projection: Literal["nls_resonance_summary"] = "nls_resonance_summary"
    module_id: Literal["radimorphic"] = "radimorphic"
    summary_label: str
    quality_band: Literal["low", "steady", "high"]
    top_resonances: list[RadiMorphicResonance] = Field(min_length=1, max_length=3)
    raw_debug_excluded: Literal[True] = True


class RadiMorphicTherapistProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["therapist"] = "therapist"
    projection: Literal["nls_profile_detail"] = "nls_profile_detail"
    module_id: Literal["radimorphic"] = "radimorphic"
    top_resonances: list[RadiMorphicResonance] = Field(min_length=1, max_length=20)
    metrics: RadiMorphicScanMetrics
    therapist_notes: list[str] = Field(min_length=1)
    raw_debug_excluded: Literal[True] = True


class RadiMorphicAdminProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin"] = "admin"
    projection: Literal["operational_summary"] = "operational_summary"
    module_id: Literal["radimorphic"] = "radimorphic"
    job: dict[str, Any]
    execution: dict[str, Any]
    raw_debug_excluded: Literal[True] = True
