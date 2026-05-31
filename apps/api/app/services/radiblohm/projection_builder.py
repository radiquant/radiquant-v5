"""RadiBlohm role projection builder."""

from __future__ import annotations

from app.schemas.radiblohm import (
    RadiBlohmAdminProjection,
    RadiBlohmClientProjection,
    RadiBlohmResultPayload,
    RadiBlohmRole,
    RadiBlohmTherapistProjection,
)

FORBIDDEN_PROJECTION_KEYS = {
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
    "result_payload_json",
}


class RadiBlohmProjectionError(ValueError):
    """Raised when a RadiBlohm projection would expose unsafe data."""

    public_detail = "RadiBlohm projection rejected"

    def __init__(self, reason: str) -> None:
        super().__init__(self.public_detail)
        self.reason = reason


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


def _coherence_band(score: float) -> str:
    if score < 0.34:
        return "low"
    if score < 0.74:
        return "steady"
    return "high"


class RadiBlohmProjectionBuilder:
    """Build role-safe RadiBlohm projections without returning raw payloads."""

    def build_projection(
        self,
        *,
        payload: RadiBlohmResultPayload,
        role: RadiBlohmRole,
    ) -> RadiBlohmClientProjection | RadiBlohmTherapistProjection | RadiBlohmAdminProjection:
        self._validate_payload(payload)
        if role == "client":
            return RadiBlohmClientProjection(
                summary_label="RadiBlohm morphic field summary is available for guided review.",
                coherence_band=_coherence_band(
                    payload.morphic_field.coherence
                ),  # type: ignore[arg-type]
                field_strength=payload.morphic_field.field_strength,
                resonance_frequency=payload.morphic_field.resonance_frequency,
            )
        if role == "therapist":
            return RadiBlohmTherapistProjection(
                morphic_field=payload.morphic_field,
                geometry=payload.geometry,
                tcm=payload.tcm,
                therapist_notes=[
                    "Review field strength and coherence in the wellbeing session context.",
                    "Interpret morphic field values as non-medical wellbeing signals only.",
                ],
            )
        return RadiBlohmAdminProjection(
            job={
                "module_run_id": str(payload.module_run_id),
                "tenant_id": str(payload.tenant_id),
                "session_id": str(payload.session_id),
                "workflow_run_id": str(payload.workflow_run_id),
            },
            execution={
                "compute_backend": payload.compute_backend,
                "hardware_entropy_enabled": payload.hardware_entropy_enabled,
                "entropy_source": payload.entropy_source,
                "algorithm_version": payload.algorithm_version,
                "manifest_version": payload.manifest_version,
            },
        )

    def _validate_payload(self, payload: RadiBlohmResultPayload) -> None:
        forbidden = _contains_forbidden_key(payload.model_dump(mode="json"))
        if forbidden is not None:
            raise RadiBlohmProjectionError(f"forbidden_projection_key:{forbidden}")
        if payload.compute_backend != "cpu":
            raise RadiBlohmProjectionError("cpu_backend_required")
        if payload.hardware_entropy_enabled is not False:
            raise RadiBlohmProjectionError("hardware_entropy_must_remain_stubbed")
