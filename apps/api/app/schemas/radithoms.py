"""RadiThoms API, result, and projection schemas."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RadiThomsRole = Literal["client", "therapist", "admin"]
RadiThomsJobStatus = Literal["queued", "storage_ready", "result_stored", "failed_closed"]
RadiThomsElement = Literal["wood", "fire", "earth", "metal", "water"]
RadiThomsYinYang = Literal["yin", "yang"]


class RadiThomsClientVector5D(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    z: float = Field(ge=0, le=1)
    w: float = Field(ge=0, le=1)
    t: float = Field(ge=0, le=1)


class RadiThomsMeridianBalance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meridian_name: str
    element: RadiThomsElement
    yin_yang: RadiThomsYinYang
    balance_score: float = Field(ge=-1, le=1)
    energy_level: float = Field(ge=0, le=100)


class RadiThomsAcupuncturePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    point_id: str
    name: str
    meridian: str
    frequency_hz: float = Field(ge=0)
    location: str
    activation_score: float = Field(ge=0, le=1)


class RadiThomsAttractorProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_attractor: str
    attractor_stability: float = Field(ge=0, le=1)
    catastrophe_risk: float = Field(ge=0, le=1)


class RadiThomsResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["radithoms_result_v1"] = "radithoms_result_v1"
    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    module_id: Literal["radithoms"] = "radithoms"
    algorithm_version: Literal["radithoms-v5-vector-meridian-v1"] = (
        "radithoms-v5-vector-meridian-v1"
    )
    manifest_version: str = Field(min_length=1, max_length=80)
    compute_backend: Literal["cpu"] = "cpu"
    hardware_entropy_enabled: Literal[False] = False
    entropy_source: Literal["os.urandom_stub"] = "os.urandom_stub"
    field_signature: str = Field(min_length=16, max_length=16)
    client_vector: RadiThomsClientVector5D
    meridian_balances: list[RadiThomsMeridianBalance] = Field(min_length=12, max_length=12)
    dominant_element: RadiThomsElement
    recommended_points: list[RadiThomsAcupuncturePoint] = Field(min_length=1, max_length=5)
    attractor: RadiThomsAttractorProfile
    primary_frequency_hz: float = Field(ge=0)
    harmonic_frequencies: list[float] = Field(min_length=1, max_length=5)
    projection_status: Literal["pending_projection_builder"] = "pending_projection_builder"


class RadiThomsJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    workflow_run_id: UUID
    workflow_step_run_id: UUID
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)


class RadiThomsJobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: Literal["radithoms"] = "radithoms"
    tenant_id: UUID
    job_id: UUID | None = None
    session_id: UUID | None = None
    workflow_run_id: UUID | None = None
    workflow_step_run_id: UUID | None = None
    job_status: RadiThomsJobStatus | None = None
    route_status: Literal["job_record_created", "job_record_found"] = "job_record_found"
    message: str = Field(max_length=200)


class RadiThomsClientProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["client"] = "client"
    projection: Literal["meridian_balance_summary"] = "meridian_balance_summary"
    module_id: Literal["radithoms"] = "radithoms"
    summary_label: str
    dominant_element: RadiThomsElement
    current_attractor: str
    primary_frequency_hz: float = Field(ge=0)
    raw_debug_excluded: Literal[True] = True


class RadiThomsTherapistProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["therapist"] = "therapist"
    projection: Literal["meridian_balance_detail"] = "meridian_balance_detail"
    module_id: Literal["radithoms"] = "radithoms"
    client_vector: RadiThomsClientVector5D
    meridian_balances: list[RadiThomsMeridianBalance] = Field(min_length=12, max_length=12)
    dominant_element: RadiThomsElement
    recommended_points: list[RadiThomsAcupuncturePoint] = Field(min_length=1, max_length=5)
    attractor: RadiThomsAttractorProfile
    therapist_notes: list[str] = Field(min_length=1)
    raw_debug_excluded: Literal[True] = True


class RadiThomsAdminProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin"] = "admin"
    projection: Literal["operational_summary"] = "operational_summary"
    module_id: Literal["radithoms"] = "radithoms"
    job: dict[str, Any]
    execution: dict[str, Any]
    raw_debug_excluded: Literal[True] = True
