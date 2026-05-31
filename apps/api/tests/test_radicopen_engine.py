"""RadiCopen engine domain tests."""

import sys
from pathlib import Path
from uuid import uuid4

import pytest

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.services.radicopen.engine import (  # noqa: E402
    RadiCopenEngine,
    RadiCopenExecutionInput,
    _adaptive_fibonacci_pairs,
    calculate_level_resonance,
    generate_rate_data,
    normalize_word,
)


def test_normalize_word_handles_umlauts_and_potency_suffix() -> None:
    assert normalize_word("Ärnica C30") == "AERNICA"


def test_adaptive_fibonacci_pairs_by_length() -> None:
    assert _adaptive_fibonacci_pairs(4) == (13, 21)
    assert _adaptive_fibonacci_pairs(10) == (21, 34)
    assert _adaptive_fibonacci_pairs(20) == (34, 55)
    assert _adaptive_fibonacci_pairs(21) == (55, 89)


def test_generate_rate_data_uses_weighted_a1_z26_sum() -> None:
    rate = generate_rate_data(
        word="ABC",
        potency=1,
        potency_type="D",
        kozyrev_factor=1.0,
    )

    assert rate.primary_sum == 14
    assert rate.base_rate == 14000
    assert rate.fibonacci_pair == "13/21"
    assert rate.final_rate > rate.fibonacci_rate


def test_generate_rate_data_rejects_empty_normalized_word() -> None:
    with pytest.raises(ValueError, match="word_required_after_normalization"):
        generate_rate_data(word="!!!", kozyrev_factor=1.0)


def test_level_resonance_returns_13_levels_and_highest_level() -> None:
    resonance = calculate_level_resonance(copen_rate=1_250_000, word="meridian balance")

    assert len(resonance.levels) == 13
    assert 1 <= resonance.highest_level <= 13
    assert resonance.highest_level_value >= 0


def test_level_resonance_keyword_bonus_can_reach_level() -> None:
    resonance = calculate_level_resonance(copen_rate=50_000, word="atom particle")

    assert resonance.levels[0].value >= 50


def test_engine_execute_is_cpu_only_and_stubbed_entropy() -> None:
    payload = RadiCopenEngine(seed=123).execute(
        RadiCopenExecutionInput(
            module_run_id=uuid4(),
            tenant_id=uuid4(),
            client_id=uuid4(),
            session_id=uuid4(),
            workflow_run_id=uuid4(),
            goal_title="Morphic Balance",
            goal_description="Centered session",
            client_display_name="Client A",
        )
    )

    assert payload.compute_backend == "cpu"
    assert payload.hardware_entropy_enabled is False
    assert payload.entropy_source == "os.urandom_stub"
    assert payload.rate.final_rate > 0
    assert len(payload.level_distribution) == 13
