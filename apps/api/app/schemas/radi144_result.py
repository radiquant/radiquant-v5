"""Radi144 result schema DTOs.

These Pydantic models mirror the committed Radi144 result contract. They do not
persist results, expose API routes, or build client projections in this gate.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ComputeBackend = Literal["cpu", "cuda", "simulation_disabled_until_engine_gate"]


class Radi144Confidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0, le=1)
    data_quality: float = Field(ge=0, le=1)
    stability: float = Field(ge=0, le=1)
    language_scope: Literal["wellbeing_only"] = "wellbeing_only"


class Radi144SynergySeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_module: Literal["radi144"] = "radi144"
    top_labels: list[str] = Field(min_length=1, max_length=3)
    confidence_score: float = Field(ge=0, le=1)
    matrix_shape: tuple[Literal[12], Literal[12]] = (12, 12)
    seed_checksum: str = Field(min_length=16, max_length=16)


class Radi144Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    algorithm_version: str = Field(min_length=1, max_length=80)
    manifest_version: str = Field(min_length=1, max_length=80)
    input_hash: str = Field(min_length=16, max_length=128)
    reference_matrix_version: str = Field(min_length=1, max_length=80)
    compute_backend: ComputeBackend
    duration_ms: int = Field(ge=0)


class Radi144Retention(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: Literal["sensitive_module_result"] = "sensitive_module_result"
    contains_sensitive_data: Literal[True] = True
    client_projection_required: Literal[True] = True
    raw_debug_allowed: Literal[False] = False


class Radi144ClientProjectionPlaceholder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending_projection_builder"] = "pending_projection_builder"
    summary_label: str = Field(max_length=160)
    quality_label: str = Field(max_length=80)
    raw_debug_excluded: Literal[True] = True


class Radi144Result(BaseModel):
    """Contract DTO for Radi144 module results before persistence/projection gates."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["radi144_result_v1"] = "radi144_result_v1"
    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    module_id: Literal["radi144"] = "radi144"
    algorithm_version: str = Field(min_length=1, max_length=80)
    manifest_version: str = Field(min_length=1, max_length=80)
    compute_backend: ComputeBackend
    matrix_shape: tuple[Literal[12], Literal[12]] = (12, 12)
    coherence_scores: dict[str, float] = Field(min_length=12, max_length=12)
    biofield_map: dict[str, float] = Field(min_length=12, max_length=12)
    confidence: Radi144Confidence
    synergy_seed: Radi144SynergySeed
    provenance: Radi144Provenance
    retention: Radi144Retention
    client_projection: Radi144ClientProjectionPlaceholder
