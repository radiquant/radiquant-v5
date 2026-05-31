"""RadiBlohm engine domain tests."""

import sys
from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.services.radiblohm.engine import (  # noqa: E402
    RadiBlohmEngine,
    RadiBlohmExecutionInput,
    _apply_platonic_geometry,
    _apply_tcm_elements,
    _coherence,
    calculate_morphic_field,
)


def test_calculate_morphic_field_returns_bounded_superposition() -> None:
    psi, terms = calculate_morphic_field(
        time_value=0.25,
        amplitudes=np.array([0.4, 0.4, 0.4]),
        energies=np.array([1.0, 2.0, 3.0]),
    )

    assert 0 <= psi <= 1
    assert len(terms) == 3
    assert terms[0].state_index == 1


def test_calculate_morphic_field_rejects_mismatched_states() -> None:
    with pytest.raises(ValueError, match="matching_quantum_states_required"):
        calculate_morphic_field(
            time_value=0.25,
            amplitudes=np.array([0.4, 0.4]),
            energies=np.array([1.0, 2.0, 3.0]),
        )


def test_apply_platonic_geometry_modulates_field() -> None:
    value, profile = _apply_platonic_geometry(0.4, "dodecahedron")

    assert value > 0.4
    assert profile.form == "dodecahedron"
    assert 0 <= profile.modulation <= 1


def test_apply_tcm_elements_uses_sheng_and_ke_cycles() -> None:
    value, profile = _apply_tcm_elements(0.5, "holz")

    assert value > 0
    assert profile.element == "holz"
    assert profile.nourishing_element == "feuer"
    assert profile.controlling_element == "erde"


def test_coherence_is_bounded() -> None:
    score = _coherence([0.2, 0.5, 0.7, 0.9])

    assert 0 <= score <= 1


def test_engine_execute_is_cpu_only_and_stubbed_entropy() -> None:
    payload = RadiBlohmEngine(seed=123).execute(
        RadiBlohmExecutionInput(
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
    assert payload.morphic_field.field_strength >= 0
    assert payload.superposition_terms
