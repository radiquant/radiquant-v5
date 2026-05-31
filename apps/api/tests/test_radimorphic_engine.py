"""RadiMorphic engine domain tests."""

import sys
from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.schemas.radimorphic import RadiMorphicNlsProfileInput  # noqa: E402
from app.services.radimorphic.engine import (  # noqa: E402
    RadiMorphicEngine,
    RadiMorphicExecutionInput,
    _hadamard_multiplex,
    build_hadamard_s_matrix,
    encode_client_signature,
    encode_nls_profiles,
    multiplex_scan,
    nls_profile_resonance,
)


def _profiles() -> list[RadiMorphicNlsProfileInput]:
    return [
        RadiMorphicNlsProfileInput(
            item_id="p-1",
            name="cellular coherence",
            category="coherence",
            frequency_hz=432.0,
            rates=[10.0, 20.0, 30.0],
        ),
        RadiMorphicNlsProfileInput(
            item_id="p-2",
            name="hydration field",
            category="wellbeing",
            frequency_hz=528.0,
            rates=[40.0, 50.0, 60.0],
        ),
        RadiMorphicNlsProfileInput(
            item_id="p-3",
            name="sleep recovery",
            category="recovery",
            frequency_hz=741.0,
            rates=[70.0, 80.0, 90.0],
        ),
    ]


def test_hadamard_matrix_is_orthogonal_with_padding() -> None:
    matrix = build_hadamard_s_matrix(6)

    assert matrix.shape == (8, 8)
    assert np.allclose(matrix @ matrix.T, np.eye(8) * 8)


def test_hadamard_multiplex_returns_one_score_per_profile() -> None:
    signature = encode_client_signature(
        goal_title="Focus",
        goal_description="Centered session",
        client_display_name="Client A",
    )
    profile_matrix = encode_nls_profiles(_profiles())

    scores = _hadamard_multiplex(signature, profile_matrix)

    assert scores.shape == (3,)
    assert np.all(scores >= 0)


def test_multiplex_scan_returns_sorted_bounded_scores() -> None:
    signature = encode_client_signature(
        goal_title="Focus",
        goal_description="Centered session",
        client_display_name="Client A",
    )
    profile_matrix = encode_nls_profiles(_profiles())

    scores = multiplex_scan(
        client_signature=signature,
        nls_profiles=profile_matrix,
        top_k=3,
    )

    assert len(scores) == 3
    assert scores[0].resonance_score >= scores[1].resonance_score
    assert all(0 <= score.resonance_score <= 1 for score in scores)


def test_nls_profile_resonance_adds_ranked_profile_metadata() -> None:
    signature = encode_client_signature(
        goal_title="Recovery",
        goal_description="Restorative focus",
        client_display_name="Client B",
    )

    resonances = nls_profile_resonance(profiles=_profiles(), client_signature=signature, top_k=2)

    assert [resonance.rank for resonance in resonances] == [1, 2]
    assert {resonance.item_id for resonance in resonances}.issubset({"p-1", "p-2", "p-3"})


def test_engine_execute_is_cpu_only_and_stubbed_entropy() -> None:
    payload = RadiMorphicEngine(seed=123).execute(
        RadiMorphicExecutionInput(
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
    assert payload.gpu_cuda_execution_enabled is False
    assert payload.hardware_entropy_enabled is False
    assert payload.entropy_source == "os.urandom_stub"
    assert payload.top_resonances


def test_multiplex_scan_rejects_empty_profile_matrix() -> None:
    signature = np.ones(128, dtype=np.float64)

    with pytest.raises(ValueError, match="nls_profiles_required"):
        multiplex_scan(client_signature=signature, nls_profiles=np.empty((0, 128)))
