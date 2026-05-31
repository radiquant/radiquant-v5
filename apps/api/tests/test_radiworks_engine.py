"""RadiWorks engine domain tests."""

import sys
from pathlib import Path
from uuid import uuid4

import pytest

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.schemas.radiworks import RadiWorksRateInput  # noqa: E402
from app.services.radiworks.engine import RadiWorksEngine, RadiWorksExecutionInput  # noqa: E402


def _rates(count: int = 8) -> list[RadiWorksRateInput]:
    return [RadiWorksRateInput(name=f"rate_{index}", value=str(index)) for index in range(count)]


def test_analyse_rate_list_returns_ranked_rates() -> None:
    engine = RadiWorksEngine(seed=123)

    rates, vitality, trials, monte_carlo = engine.analyse_rate_list(_rates())

    assert rates
    assert rates == sorted(rates, key=lambda item: (item.score, item.name), reverse=True)
    assert vitality >= 0
    assert trials == len(rates) * monte_carlo.trials


def test_analyse_rate_list_assigns_level_and_potency() -> None:
    engine = RadiWorksEngine(seed=123)

    rates, _vitality, _trials, _monte_carlo = engine.analyse_rate_list(_rates())

    assert all(1 <= rate.level <= 12 for rate in rates)
    assert all(rate.potency for rate in rates)


def test_monte_carlo_scoring_is_bounded() -> None:
    engine = RadiWorksEngine(seed=456)

    result = engine.monte_carlo_scoring(_rates(5), trials=12)

    assert result.summary.trials == 12
    assert set(result.scores) == {f"rate_{index}" for index in range(5)}
    assert all(0 <= score <= 1 for score in result.scores.values())


def test_general_vitality_check_is_bounded() -> None:
    engine = RadiWorksEngine(seed=789)

    vitality = engine.general_vitality_check()

    assert isinstance(vitality, int)
    assert 0 <= vitality <= 10000


def test_execute_builds_result_payload_without_hardware_or_gpu() -> None:
    engine = RadiWorksEngine(seed=999)

    result = engine.execute(
        RadiWorksExecutionInput(
            module_run_id=uuid4(),
            tenant_id=uuid4(),
            client_id=uuid4(),
            session_id=uuid4(),
            workflow_run_id=uuid4(),
            goal_title="Wellbeing focus",
        )
    )

    assert result.module_id == "radiworks"
    assert result.compute_backend == "cpu"
    assert result.hardware_entropy_enabled is False
    assert result.entropy_source == "os.urandom_stub"
    assert result.rates


def test_analyse_rate_list_rejects_empty_rates() -> None:
    engine = RadiWorksEngine(seed=123)

    with pytest.raises(ValueError, match="rates_required"):
        engine.analyse_rate_list([])
