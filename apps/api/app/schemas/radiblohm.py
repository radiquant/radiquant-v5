"""RadiBlohm API, result, and projection schemas."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RadiBlohmRole = Literal["client", "therapist", "admin"]
RadiBlohmJobStatus = Literal["queued", "storage_ready", "result_stored", "failed_closed"]
RadiBlohmGeometry = Literal[
    "tetrahedron",
    "cube",
    "octahedron",
    "dodecahedron",
    "icosahedron",
    "flower_of_life",
]
RadiBlohmTcmElement = Literal["holz", "feuer", "erde", "metall", "wasser"]


class RadiBlohmSuperpositionTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state_index: int = Field(ge=1)
    amplitude: float
    energy: float
    contribution: float


class RadiBlohmMorphicField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    psi_total: float = Field(ge=0, le=1)
    quantum_component: float = Field(ge=0)
    numerical_factor: float = Field(ge=0)
    geometric_factor: float = Field(ge=0)
    tcm_factor: float = Field(ge=0)
    field_strength: float = Field(ge=0, le=1)
    coherence: float = Field(ge=0, le=1)
    resonance_frequency: float = Field(ge=0)


class RadiBlohmGeometryProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    form: RadiBlohmGeometry
    factor: float = Field(ge=0)
    modulation: float = Field(ge=0, le=1)


class RadiBlohmTcmProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element: RadiBlohmTcmElement
    factor: float = Field(ge=0)
    nourishing_element: RadiBlohmTcmElement
    controlling_element: RadiBlohmTcmElement
    modulation: float = Field(ge=0, le=1)


class RadiBlohmResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["radiblohm_result_v1"] = "radiblohm_result_v1"
    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    module_id: Literal["radiblohm"] = "radiblohm"
    algorithm_version: Literal["radiblohm-v5-morphic-field-v1"] = (
        "radiblohm-v5-morphic-field-v1"
    )
    manifest_version: str = Field(min_length=1, max_length=80)
    compute_backend: Literal["cpu"] = "cpu"
    hardware_entropy_enabled: Literal[False] = False
    entropy_source: Literal["os.urandom_stub"] = "os.urandom_stub"
    morphic_field: RadiBlohmMorphicField
    geometry: RadiBlohmGeometryProfile
    tcm: RadiBlohmTcmProfile
    superposition_terms: list[RadiBlohmSuperpositionTerm] = Field(min_length=1, max_length=12)
    projection_status: Literal["pending_projection_builder"] = "pending_projection_builder"


class RadiBlohmJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    workflow_run_id: UUID
    workflow_step_run_id: UUID
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)


class RadiBlohmJobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_id: Literal["radiblohm"] = "radiblohm"
    tenant_id: UUID
    job_id: UUID | None = None
    session_id: UUID | None = None
    workflow_run_id: UUID | None = None
    workflow_step_run_id: UUID | None = None
    job_status: RadiBlohmJobStatus | None = None
    route_status: Literal["job_record_created", "job_record_found"] = "job_record_found"
    message: str = Field(max_length=200)


class RadiBlohmClientProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["client"] = "client"
    projection: Literal["morphic_field_summary"] = "morphic_field_summary"
    module_id: Literal["radiblohm"] = "radiblohm"
    summary_label: str
    coherence_band: Literal["low", "steady", "high"]
    field_strength: float = Field(ge=0, le=1)
    resonance_frequency: float = Field(ge=0)
    raw_debug_excluded: Literal[True] = True


class RadiBlohmTherapistProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["therapist"] = "therapist"
    projection: Literal["morphic_field_detail"] = "morphic_field_detail"
    module_id: Literal["radiblohm"] = "radiblohm"
    morphic_field: RadiBlohmMorphicField
    geometry: RadiBlohmGeometryProfile
    tcm: RadiBlohmTcmProfile
    therapist_notes: list[str] = Field(min_length=1)
    raw_debug_excluded: Literal[True] = True


class RadiBlohmAdminProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin"] = "admin"
    projection: Literal["operational_summary"] = "operational_summary"
    module_id: Literal["radiblohm"] = "radiblohm"
    job: dict[str, Any]
    execution: dict[str, Any]
    raw_debug_excluded: Literal[True] = True
