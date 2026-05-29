"""Radi144 role projection builder.

Projection Builder Gate scope: build safe client/therapist projections from an
already validated Radi144Result payload. This service is not wired to API
routes, frontend UI, workers, or engine execution.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.radi144_result import Radi144Result

FORBIDDEN_PROJECTION_KEYS = {
    "raw_resonance_matrix",
    "normalized_matrix",
    "client_vector",
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
}
Radi144ProjectionRole = Literal["client", "therapist"]


class Radi144ProjectionError(ValueError):
    """Raised when a projection would violate safety or privacy rules."""

    public_detail = "Radi144 projection rejected"

    def __init__(self, reason: str) -> None:
        super().__init__(self.public_detail)
        self.reason = reason


class Radi144ClientProjection(BaseModel):
    """Calm client-facing summary with no raw/debug/internal data."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["client"] = "client"
    projection: Literal["calm_summary"] = "calm_summary"
    module_id: Literal["radi144"] = "radi144"
    summary_label: str = Field(max_length=160)
    quality_label: str = Field(max_length=80)
    confidence_band: Literal["low", "medium", "steady"]
    wellbeing_focus_labels: list[str] = Field(min_length=1, max_length=3)
    next_step_hint: str = Field(max_length=160)
    raw_debug_excluded: Literal[True] = True


class Radi144TherapistProjection(BaseModel):
    """Professional detail projection that still excludes raw/debug/internal data."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["therapist"] = "therapist"
    projection: Literal["professional_detail"] = "professional_detail"
    module_id: Literal["radi144"] = "radi144"
    coherence_scores: dict[str, float]
    biofield_map: dict[str, float]
    confidence: dict[str, float | str]
    provenance: dict[str, object]
    retention: dict[str, object]
    therapist_approval_gates: list[str] = Field(min_length=1)
    raw_debug_excluded: Literal[True] = True


def _contains_forbidden_key(value: object) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_PROJECTION_KEYS:
                return key
            found = _contains_forbidden_key(nested)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _contains_forbidden_key(nested)
            if found is not None:
                return found
    return None


def _confidence_band(score: float) -> Literal["low", "medium", "steady"]:
    if score < 0.4:
        return "low"
    if score < 0.7:
        return "medium"
    return "steady"


class Radi144ProjectionBuilder:
    """Build role-safe Radi144 projections without side effects."""

    def build_client_projection(self, result: Radi144Result) -> Radi144ClientProjection:
        self._validate_result(result)
        focus_labels = list(result.biofield_map)[:3]
        confidence_score = float(result.confidence.score)
        return Radi144ClientProjection(
            summary_label=result.client_projection.summary_label,
            quality_label=result.client_projection.quality_label,
            confidence_band=_confidence_band(confidence_score),
            wellbeing_focus_labels=focus_labels,
            next_step_hint="Besprechen Sie die Wellbeing-Zusammenfassung im geschützten Sitzungskontext.",
        )

    def build_therapist_projection(self, result: Radi144Result) -> Radi144TherapistProjection:
        self._validate_result(result)
        return Radi144TherapistProjection(
            coherence_scores=result.coherence_scores,
            biofield_map=result.biofield_map,
            confidence=result.confidence.model_dump(mode="json"),
            provenance=result.provenance.model_dump(mode="json"),
            retention=result.retention.model_dump(mode="json"),
            therapist_approval_gates=["review_projection", "confirm_wellbeing_language", "approve_client_summary"],
        )

    def build_projection(
        self,
        *,
        result: Radi144Result,
        role: Radi144ProjectionRole,
    ) -> Radi144ClientProjection | Radi144TherapistProjection:
        if role == "client":
            return self.build_client_projection(result)
        return self.build_therapist_projection(result)

    def _validate_result(self, result: Radi144Result) -> None:
        payload = result.model_dump(mode="json")
        forbidden = _contains_forbidden_key(payload)
        if forbidden is not None:
            raise Radi144ProjectionError(f"forbidden_projection_key:{forbidden}")
        if result.client_projection.raw_debug_excluded is not True:
            raise Radi144ProjectionError("raw_debug_must_be_excluded")
        if result.retention.raw_debug_allowed is not False:
            raise Radi144ProjectionError("raw_debug_must_remain_forbidden")
        if result.confidence.language_scope != "wellbeing_only":
            raise Radi144ProjectionError("wellbeing_language_required")
