"""RadiCopen role projection builder."""

from __future__ import annotations

from app.schemas.radicopen import (
    RadiCopenAdminProjection,
    RadiCopenClientProjection,
    RadiCopenResultPayload,
    RadiCopenRole,
    RadiCopenTherapistProjection,
)

FORBIDDEN_PROJECTION_KEYS = {
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
    "result_payload_json",
}


class RadiCopenProjectionError(ValueError):
    """Raised when a RadiCopen projection would expose unsafe data."""

    public_detail = "RadiCopen projection rejected"

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


class RadiCopenProjectionBuilder:
    """Build role-safe RadiCopen projections without returning raw payloads."""

    def build_projection(
        self,
        *,
        payload: RadiCopenResultPayload,
        role: RadiCopenRole,
    ) -> RadiCopenClientProjection | RadiCopenTherapistProjection | RadiCopenAdminProjection:
        self._validate_payload(payload)
        if role == "client":
            return RadiCopenClientProjection(
                summary_label="RadiCopen Copen-rate analysis is available for guided review.",
                final_rate=payload.rate.final_rate,
                highest_level=payload.level_resonance.highest_level,
                highest_level_name=payload.level_resonance.highest_level_name,
            )
        if role == "therapist":
            return RadiCopenTherapistProjection(
                rate=payload.rate,
                level_resonance=payload.level_resonance,
                dominant_level=payload.dominant_level,
                therapist_notes=[
                    "Review final rate and level resonance in the wellbeing session context.",
                    "Keep interpretation non-medical and client-safe.",
                ],
            )
        return RadiCopenAdminProjection(
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

    def _validate_payload(self, payload: RadiCopenResultPayload) -> None:
        forbidden = _contains_forbidden_key(payload.model_dump(mode="json"))
        if forbidden is not None:
            raise RadiCopenProjectionError(f"forbidden_projection_key:{forbidden}")
        if payload.compute_backend != "cpu":
            raise RadiCopenProjectionError("cpu_backend_required")
        if payload.hardware_entropy_enabled is not False:
            raise RadiCopenProjectionError("hardware_entropy_must_remain_stubbed")
