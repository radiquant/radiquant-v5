"""Radi144 CPU-safe execution gate tests."""

from uuid import uuid4

import pytest

from app.schemas.radi144_result import Radi144Result


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(nested, key) for nested in value.values())
    if isinstance(value, list):
        return any(_contains_key(nested, key) for nested in value)
    return False
from app.services.radi144.cpu_safe_execution import Radi144CpuSafeExecutionInput, Radi144CpuSafeExecutionService
from app.services.radi144.domain import Radi144DomainError


def _execution_input() -> Radi144CpuSafeExecutionInput:
    return Radi144CpuSafeExecutionInput(
        module_run_id=uuid4(),
        tenant_id=uuid4(),
        client_id=uuid4(),
        session_id=uuid4(),
        workflow_run_id=uuid4(),
        goal_title="Calm focus",
        goal_description="Support a centered wellbeing session.",
        client_display_name="Client A",
    )


def test_cpu_safe_execution_returns_valid_result() -> None:
    result = Radi144CpuSafeExecutionService().execute(_execution_input())

    assert isinstance(result, Radi144Result)
    assert result.compute_backend == "cpu"
    assert result.provenance.compute_backend == "cpu"
    assert result.matrix_shape == (12, 12)
    assert len(result.coherence_scores) == 12
    assert len(result.biofield_map) == 12
    assert result.confidence.language_scope == "wellbeing_only"
    assert result.retention.raw_debug_allowed is False
    assert result.client_projection.status == "pending_projection_builder"


def test_cpu_safe_execution_is_deterministic_for_same_input() -> None:
    execution_input = _execution_input()
    service = Radi144CpuSafeExecutionService()

    first = service.execute(execution_input)
    second = service.execute(execution_input)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_cpu_safe_execution_excludes_raw_debug_payload_keys() -> None:
    payload = Radi144CpuSafeExecutionService().execute(_execution_input()).model_dump(mode="json")

    for forbidden in ["raw_debug", "debug_json", "internal_state", "access_token", "password", "raw_resonance_matrix", "normalized_matrix", "client_vector"]:
        assert not _contains_key(payload, forbidden)


def test_cpu_safe_execution_requires_analysis_consent_purpose() -> None:
    execution_input = _execution_input()
    invalid = Radi144CpuSafeExecutionInput(**{**execution_input.__dict__, "consent_purpose": "other"})

    with pytest.raises(Radi144DomainError):
        Radi144CpuSafeExecutionService().execute(invalid)
