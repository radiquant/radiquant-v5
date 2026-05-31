"""RadiThoms role projection builder."""

from __future__ import annotations

from app.schemas.radithoms import (
    RadiThomsAdminProjection,
    RadiThomsClientProjection,
    RadiThomsResultPayload,
    RadiThomsRole,
    RadiThomsTherapistProjection,
)

FORBIDDEN_PROJECTION_KEYS = {
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
    "result_payload_json",
}


class RadiThomsProjectionError(ValueError):
    """Raised when a RadiThoms projection would expose unsafe data."""

    public_detail = "RadiThoms projection rejected"

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


class RadiThomsProjectionBuilder:
    """Build role-safe RadiThoms projections without returning raw payloads."""

    def build_projection(
        self,
        *,
        payload: RadiThomsResultPayload,
        role: RadiThomsRole,
    ) -> RadiThomsClientProjection | RadiThomsTherapistProjection | RadiThomsAdminProjection:
        self._validate_payload(payload)
        if role == "client":
            return RadiThomsClientProjection(
                summary_label="RadiThoms meridian balance is available for guided review.",
                dominant_element=payload.dominant_element,
                current_attractor=payload.attractor.current_attractor,
                primary_frequency_hz=payload.primary_frequency_hz,
            )
        if role == "therapist":
            return RadiThomsTherapistProjection(
                client_vector=payload.client_vector,
                meridian_balances=payload.meridian_balances,
                dominant_element=payload.dominant_element,
                recommended_points=payload.recommended_points,
                attractor=payload.attractor,
                therapist_notes=[
                    "Review lower energy meridians in the wellbeing session context.",
                    "Keep interpretation non-medical and client-safe.",
                ],
            )
        return RadiThomsAdminProjection(
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

    def _validate_payload(self, payload: RadiThomsResultPayload) -> None:
        forbidden = _contains_forbidden_key(payload.model_dump(mode="json"))
        if forbidden is not None:
            raise RadiThomsProjectionError(f"forbidden_projection_key:{forbidden}")
        if payload.compute_backend != "cpu":
            raise RadiThomsProjectionError("cpu_backend_required")
        if payload.hardware_entropy_enabled is not False:
            raise RadiThomsProjectionError("hardware_entropy_must_remain_stubbed")
