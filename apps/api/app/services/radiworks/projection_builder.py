"""RadiWorks role projection builder."""

from __future__ import annotations

from app.schemas.radiworks import (
    RadiWorksAdminProjection,
    RadiWorksClientProjection,
    RadiWorksResultPayload,
    RadiWorksRole,
    RadiWorksTherapistProjection,
)

FORBIDDEN_PROJECTION_KEYS = {
    "raw_debug",
    "debug_json",
    "internal_state",
    "access_token",
    "password",
    "result_payload_json",
}


class RadiWorksProjectionError(ValueError):
    """Raised when a RadiWorks projection would expose unsafe data."""

    public_detail = "RadiWorks projection rejected"

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


def _vitality_band(score: int) -> str:
    if score < 350:
        return "low"
    if score < 750:
        return "steady"
    return "high"


class RadiWorksProjectionBuilder:
    """Build role-safe RadiWorks projections without returning raw payloads."""

    def build_projection(
        self,
        *,
        payload: RadiWorksResultPayload,
        role: RadiWorksRole,
    ) -> RadiWorksClientProjection | RadiWorksTherapistProjection | RadiWorksAdminProjection:
        self._validate_payload(payload)
        if role == "client":
            return RadiWorksClientProjection(
                summary_label="RadiWorks rate analysis is available for guided review.",
                vitality_band=_vitality_band(payload.general_vitality),
                top_rates=payload.rates[:3],
            )
        if role == "therapist":
            return RadiWorksTherapistProjection(
                rates=payload.rates[:20],
                general_vitality=payload.general_vitality,
                monte_carlo=payload.monte_carlo,
                therapist_notes=[
                    "Review rate ordering in the wellbeing session context.",
                    "Confirm language remains non-medical and client-safe.",
                ],
            )
        return RadiWorksAdminProjection(
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

    def _validate_payload(self, payload: RadiWorksResultPayload) -> None:
        forbidden = _contains_forbidden_key(payload.model_dump(mode="json"))
        if forbidden is not None:
            raise RadiWorksProjectionError(f"forbidden_projection_key:{forbidden}")
        if payload.compute_backend != "cpu":
            raise RadiWorksProjectionError("cpu_backend_required")
        if payload.hardware_entropy_enabled is not False:
            raise RadiWorksProjectionError("hardware_entropy_must_remain_stubbed")
