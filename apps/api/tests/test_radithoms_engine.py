"""RadiThoms engine domain tests."""

import sys
from pathlib import Path
from uuid import uuid4

import pytest

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.services.radithoms.engine import (  # noqa: E402
    RadiThomsEngine,
    RadiThomsExecutionInput,
    _analyze_meridians,
    _calculate_client_vector,
    _catastrophe_attractors,
    _dominant_element,
)


def test_calculate_client_vector_returns_5d_bounded_values() -> None:
    vector = _calculate_client_vector(
        client_name="Client A",
        birth_date="1980-01-15",
        signature="1234567890abcdef",
    )

    assert 0 <= vector.x <= 1
    assert 0 <= vector.y <= 1
    assert 0 <= vector.z <= 1
    assert 0 <= vector.w <= 1
    assert 0 <= vector.t <= 1


def test_calculate_client_vector_applies_resonance_safely() -> None:
    base = _calculate_client_vector(
        client_name="Client A",
        birth_date="1980-01-15",
        signature="1234567890abcdef",
    )
    shifted = _calculate_client_vector(
        client_name="Client A",
        birth_date="1980-01-15",
        signature="1234567890abcdef",
        resonance_score=0.8,
    )

    assert shifted.x >= base.x
    assert shifted.y >= base.y
    assert shifted.z >= base.z


def test_analyze_meridians_returns_12_balances() -> None:
    vector = _calculate_client_vector(
        client_name="Client A",
        birth_date="1980-01-15",
        signature="1234567890abcdef",
    )

    balances = _analyze_meridians(vector)

    assert len(balances) == 12
    assert all(-1 <= balance.balance_score <= 1 for balance in balances)
    assert {balance.yin_yang for balance in balances} == {"yin", "yang"}


def test_dominant_element_is_from_tcm_elements() -> None:
    vector = _calculate_client_vector(
        client_name="Client A",
        birth_date="1980-01-15",
        signature="1234567890abcdef",
    )

    dominant = _dominant_element(_analyze_meridians(vector))

    assert dominant in {"wood", "fire", "earth", "metal", "water"}


def test_catastrophe_attractors_are_bounded() -> None:
    vector = _calculate_client_vector(
        client_name="Client A",
        birth_date="1980-01-15",
        signature="1234567890abcdef",
    )

    attractor = _catastrophe_attractors(vector)

    assert attractor.current_attractor
    assert 0 <= attractor.attractor_stability <= 1
    assert 0 <= attractor.catastrophe_risk <= 1


def test_engine_analyze_is_cpu_only_and_stubbed_entropy() -> None:
    payload = RadiThomsEngine(seed=123).analyze(
        RadiThomsExecutionInput(
            module_run_id=uuid4(),
            tenant_id=uuid4(),
            client_id=uuid4(),
            session_id=uuid4(),
            workflow_run_id=uuid4(),
            goal_title="Wellbeing focus",
            goal_description="Centered session",
            client_display_name="Client A",
        )
    )

    assert payload.compute_backend == "cpu"
    assert payload.hardware_entropy_enabled is False
    assert payload.entropy_source == "os.urandom_stub"
    assert len(payload.field_signature) == 16
    assert len(payload.meridian_balances) == 12


def test_client_vector_rejects_invalid_birth_date() -> None:
    with pytest.raises(ValueError):
        _calculate_client_vector(
            client_name="Client A",
            birth_date="not-a-date",
            signature="1234567890abcdef",
        )
