"""RadiWorks CPU-only rate-analysis engine."""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from app.schemas.radiworks import (
    RadiWorksMonteCarloSummary,
    RadiWorksRateInput,
    RadiWorksRateScore,
    RadiWorksResultPayload,
)

POTENCIES = (
    "D1",
    "D3",
    "D6",
    "D12",
    "D30",
    "D200",
    "C1",
    "C3",
    "C6",
    "C12",
    "C30",
    "C200",
    "LM1",
    "LM6",
)


@dataclass(frozen=True)
class RadiWorksExecutionInput:
    """Tenant-scoped input for CPU-only RadiWorks execution."""

    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    goal_title: str
    goal_description: str = ""
    client_display_name: str = ""
    client_code: str | None = None
    manifest_version: str = "1.0.0"


class RadiWorksEntropy:
    """Hotbits replacement using deterministic seeds or os.urandom fallback."""

    def __init__(self, *, seed: int | None = None) -> None:
        if os.getenv("RQ5_HARDWARE_ENTROPY", "false").lower() == "true":
            seed = seed if seed is not None else int.from_bytes(os.urandom(16), "big")
        elif seed is None:
            seed = int.from_bytes(os.urandom(16), "big")
        self._rng = random.Random(int(seed))

    def integer(self, minimum: int, maximum: int | None = None) -> int:
        if maximum is None:
            return self._rng.randrange(minimum + 1)
        return minimum + self._rng.randrange(maximum - minimum + 1)

    def fraction(self) -> float:
        return self._rng.random()

    def boolean(self) -> bool:
        return self._rng.randrange(2) == 1


@dataclass(frozen=True)
class MonteCarloResult:
    scores: dict[str, float]
    summary: RadiWorksMonteCarloSummary


class RadiWorksEngine:
    """Ported RadiWorks algorithms without hardware or GPU dependencies."""

    def __init__(self, *, seed: int | None = None) -> None:
        self.entropy = RadiWorksEntropy(seed=seed)
        self.max_value = 100

    def analyse_rate_list(
        self,
        rates: list[RadiWorksRateInput],
        *,
        very_high_max_hit: bool = False,
        isolation_mode: bool = True,
        synergy_buffer: dict[str, object] | None = None,
        monte_carlo_trials: int = 96,
    ) -> tuple[list[RadiWorksRateScore], int, int, RadiWorksMonteCarloSummary]:
        """Select, score, and rank rates with os.urandom-backed stochastic entropy."""
        if not rates:
            raise ValueError("rates_required")
        self.max_value = 1000 if very_high_max_hit else 100
        shuffled = self._shuffle_rates(list(rates))
        subset_size = min(
            len(shuffled),
            self._subset_size(len(shuffled), isolation_mode, synergy_buffer),
        )
        selected = shuffled[:subset_size]
        monte_carlo = self.monte_carlo_scoring(selected, trials=monte_carlo_trials)
        scored: list[RadiWorksRateScore] = []
        scoring_trials = 0

        for rate in selected:
            normalized = monte_carlo.scores[rate.name]
            score = max(1, int(round(normalized * self.max_value)))
            scoring_trials += monte_carlo_trials
            scored.append(
                RadiWorksRateScore(
                    name=rate.name,
                    score=score,
                    normalized_score=round(normalized, 6),
                    level=self._level_for_score(normalized),
                    potency=self._potency(),
                    rate=rate.value,
                    url=rate.url,
                )
            )

        scored.sort(key=lambda item: (item.score, item.name), reverse=True)
        return scored[:105], self.general_vitality_check(), scoring_trials, monte_carlo.summary

    def monte_carlo_scoring(
        self,
        rates: list[RadiWorksRateInput],
        *,
        trials: int = 96,
    ) -> MonteCarloResult:
        """Run CPU-only Monte-Carlo scoring for candidate rates."""
        if not rates:
            raise ValueError("rates_required")
        if trials < 1:
            raise ValueError("trials_must_be_positive")

        totals = {rate.name: 0.0 for rate in rates}
        for trial in range(1, trials + 1):
            drift = self.entropy.fraction()
            for index, rate in enumerate(rates, start=1):
                base = self.entropy.fraction()
                phase = ((trial * index) % 17) / 17
                totals[rate.name] += (base * 0.7) + (drift * 0.2) + (phase * 0.1)

        raw_scores = {name: value / trials for name, value in totals.items()}
        maximum = max(raw_scores.values()) or 1.0
        normalized = {name: min(1.0, value / maximum) for name, value in raw_scores.items()}
        values = list(normalized.values())
        mean_score = sum(values) / len(values)
        variance = sum((value - mean_score) ** 2 for value in values) / len(values)
        stability = max(0.0, 1.0 - variance)
        return MonteCarloResult(
            scores=normalized,
            summary=RadiWorksMonteCarloSummary(
                trials=trials,
                mean_score=round(mean_score, 6),
                max_score=round(max(values), 6),
                stability=round(stability, 6),
            ),
        )

    def general_vitality_check(self) -> int:
        """Calculate a bounded general vitality score."""
        samples = sorted((self.entropy.integer(0, 1000) for _ in range(3)), reverse=True)
        vitality = samples[0]
        while vitality > 950:
            bonus = self.entropy.integer(0, 100)
            if bonus < 50:
                break
            vitality += bonus
        return min(vitality, 10000)

    def execute(self, execution_input: RadiWorksExecutionInput) -> RadiWorksResultPayload:
        """Build a validated RadiWorks result payload without persistence."""
        rates, vitality, trials, monte_carlo = self.analyse_rate_list(
            self._rates_from_context(execution_input)
        )
        return RadiWorksResultPayload(
            module_run_id=execution_input.module_run_id,
            tenant_id=execution_input.tenant_id,
            client_id=execution_input.client_id,
            session_id=execution_input.session_id,
            workflow_run_id=execution_input.workflow_run_id,
            manifest_version=execution_input.manifest_version,
            rates=rates,
            general_vitality=vitality,
            monte_carlo=monte_carlo,
            trials=trials,
            top_rate_names=[rate.name for rate in rates[:10]],
        )

    def _shuffle_rates(self, rates: list[RadiWorksRateInput]) -> list[RadiWorksRateInput]:
        shuffled: list[RadiWorksRateInput] = []
        while rates:
            shuffled.append(rates.pop(self.entropy.integer(0, len(rates) - 1)))
        return shuffled

    def _subset_size(
        self,
        count: int,
        isolation_mode: bool,
        synergy_buffer: dict[str, object] | None,
    ) -> int:
        base = max(1, min(105, count))
        if not isolation_mode and synergy_buffer is not None:
            coherence = synergy_buffer.get("coherence_score")
            if isinstance(coherence, int | float):
                base = max(1, int(base * max(0.35, 1.2 - float(coherence))))
        return base

    def _level_for_score(self, normalized_score: float) -> int:
        return max(1, min(12, int(normalized_score * 12) or 1))

    def _potency(self) -> str:
        return POTENCIES[self.entropy.integer(0, len(POTENCIES) - 1)]

    def _rates_from_context(
        self,
        execution_input: RadiWorksExecutionInput,
    ) -> list[RadiWorksRateInput]:
        source = "|".join(
            [
                execution_input.goal_title,
                execution_input.goal_description,
                execution_input.client_display_name,
                execution_input.client_code or "",
            ]
        )
        digest = sha256(source.encode("utf-8")).hexdigest()
        labels = [
            "vitality",
            "coherence",
            "resilience",
            "balance",
            "integration",
            "focus",
            "restoration",
            "stability",
        ]
        return [
            RadiWorksRateInput(name=f"{label}_{index + 1}", value=digest[index * 4 : index * 4 + 4])
            for index, label in enumerate(labels)
        ]
