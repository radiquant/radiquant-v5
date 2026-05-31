"""RadiMorphic role projection builder."""

from __future__ import annotations

from app.schemas.radimorphic import (
    RadiMorphicAdminProjection,
    RadiMorphicClientProjection,
    RadiMorphicResultPayload,
    RadiMorphicRole,
    RadiMorphicTherapistProjection,
)

FORBIDDEN_PROJECTION_KEYS = {
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
    "result_payload_json",
}


class RadiMorphicProjectionError(ValueError):
    """Raised when a RadiMorphic projection would expose unsafe data."""

    public_detail = "RadiMorphic projection rejected"

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


def _quality_band(score: float) -> str:
    if score < 0.34:
        return "low"
    if score < 0.74:
        return "steady"
    return "high"


class RadiMorphicProjectionBuilder:
    """Build role-safe RadiMorphic projections without returning raw payloads."""

    def build_projection(
        self,
        *,
        payload: RadiMorphicResultPayload,
        role: RadiMorphicRole,
    ) -> (
        RadiMorphicClientProjection | RadiMorphicTherapistProjection | RadiMorphicAdminProjection
    ):
        self._validate_payload(payload)
        if role == "client":
            return RadiMorphicClientProjection(
                summary_label="RadiMorphic NLS resonance is available for guided review.",
                quality_band=_quality_band(payload.metrics.quality_score),  # type: ignore[arg-type]
                top_resonances=payload.top_resonances[:3],
            )
        if role == "therapist":
            return RadiMorphicTherapistProjection(
                top_resonances=payload.top_resonances[:20],
                metrics=payload.metrics,
                therapist_notes=[
                    "Review NLS resonance ranking in the session context.",
                    "Keep interpretation client-safe and non-medical.",
                ],
            )
        return RadiMorphicAdminProjection(
            job={
                "module_run_id": str(payload.module_run_id),
                "tenant_id": str(payload.tenant_id),
                "session_id": str(payload.session_id),
                "workflow_run_id": str(payload.workflow_run_id),
            },
            execution={
                "compute_backend": payload.compute_backend,
                "gpu_cuda_execution_enabled": payload.gpu_cuda_execution_enabled,
                "hardware_entropy_enabled": payload.hardware_entropy_enabled,
                "entropy_source": payload.entropy_source,
                "algorithm_version": payload.algorithm_version,
                "manifest_version": payload.manifest_version,
            },
        )

    def _validate_payload(self, payload: RadiMorphicResultPayload) -> None:
        forbidden = _contains_forbidden_key(payload.model_dump(mode="json"))
        if forbidden is not None:
            raise RadiMorphicProjectionError(f"forbidden_projection_key:{forbidden}")
        if payload.compute_backend != "cpu":
            raise RadiMorphicProjectionError("cpu_backend_required")
        if payload.gpu_cuda_execution_enabled is not False:
            raise RadiMorphicProjectionError("gpu_path_must_remain_disabled")
        if payload.hardware_entropy_enabled is not False:
            raise RadiMorphicProjectionError("hardware_entropy_must_remain_stubbed")
