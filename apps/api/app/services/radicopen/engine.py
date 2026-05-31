"""RadiCopen CPU-only Copen V4 rate engine."""

from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass
from uuid import UUID

from app.schemas.radicopen import (
    RadiCopenLevelData,
    RadiCopenLevelResonance,
    RadiCopenPotencyType,
    RadiCopenRateData,
    RadiCopenResultPayload,
)

LEVELS: tuple[dict[str, object], ...] = (
    {
        "id": 1,
        "name": "Physical Realm - Particles",
        "description": "Material particles and elemental structure.",
        "keywords": ("atom", "particle", "dna", "matter"),
        "frequency_min": 1.0,
        "frequency_max": 100000.0,
        "weight": 15,
    },
    {
        "id": 2,
        "name": "Physical Realm - Structure",
        "description": "Body, tissue, and structure field.",
        "keywords": ("body", "organ", "tissue", "structure"),
        "frequency_min": 100000.0,
        "frequency_max": 500000.0,
        "weight": 14,
    },
    {
        "id": 3,
        "name": "Etheric Realm - Prana",
        "description": "Life-force and breath field.",
        "keywords": ("prana", "qi", "energy", "breath"),
        "frequency_min": 500000.0,
        "frequency_max": 1000000.0,
        "weight": 13,
    },
    {
        "id": 4,
        "name": "Etheric Realm - Meridians",
        "description": "Meridian and channel field.",
        "keywords": ("meridian", "chakra", "nadi", "channel"),
        "frequency_min": 1000000.0,
        "frequency_max": 2000000.0,
        "weight": 12,
    },
    {
        "id": 5,
        "name": "Astral Realm - Emotions",
        "description": "Emotion and feeling field.",
        "keywords": ("emotion", "feeling", "affect"),
        "frequency_min": 2000000.0,
        "frequency_max": 3500000.0,
        "weight": 11,
    },
    {
        "id": 6,
        "name": "Astral Realm - Thought-Forms",
        "description": "Thought form and magnetic field.",
        "keywords": ("thought", "magnetic", "pattern"),
        "frequency_min": 3500000.0,
        "frequency_max": 5000000.0,
        "weight": 10,
    },
    {
        "id": 7,
        "name": "Mental Realm - Time",
        "description": "Time, space, and form constructs.",
        "keywords": ("time", "space", "form"),
        "frequency_min": 5000000.0,
        "frequency_max": 7000000.0,
        "weight": 9,
    },
    {
        "id": 8,
        "name": "Mental Realm - Constructs",
        "description": "Concept and mental construct field.",
        "keywords": ("concept", "mental", "idea"),
        "frequency_min": 7000000.0,
        "frequency_max": 9000000.0,
        "weight": 8,
    },
    {
        "id": 9,
        "name": "Causal Plane - Blueprints",
        "description": "Blueprint and destiny script field.",
        "keywords": ("blueprint", "destiny", "akasha"),
        "frequency_min": 9000000.0,
        "frequency_max": 11000000.0,
        "weight": 7,
    },
    {
        "id": 10,
        "name": "Causal Plane - Alchemy",
        "description": "Intention and transformation field.",
        "keywords": ("intention", "alchemy", "transformation"),
        "frequency_min": 11000000.0,
        "frequency_max": 13000000.0,
        "weight": 6,
    },
    {
        "id": 11,
        "name": "Atmic Plane - Identity",
        "description": "Essence and identity field.",
        "keywords": ("identity", "essence", "incarnation"),
        "frequency_min": 13000000.0,
        "frequency_max": 16000000.0,
        "weight": 3,
    },
    {
        "id": 12,
        "name": "Atmic Plane - Unity",
        "description": "Unity and archetypal love field.",
        "keywords": ("unity", "love", "archetype"),
        "frequency_min": 16000000.0,
        "frequency_max": 20000000.0,
        "weight": 2,
    },
    {
        "id": 13,
        "name": "Creator - Divinity",
        "description": "Creator-level high-frequency catch-all.",
        "keywords": ("creator", "divinity", "source"),
        "frequency_min": 20000000.0,
        "frequency_max": 99999999.0,
        "weight": 1,
    },
)
TOTAL_LEVEL_WEIGHT = sum(int(level["weight"]) for level in LEVELS)


@dataclass(frozen=True)
class RadiCopenExecutionInput:
    """Tenant-scoped execution context for a RadiCopen queued job."""

    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    goal_title: str
    goal_description: str
    client_display_name: str
    client_code: str | None = None
    manifest_version: str = "1.0.0"
    word: str | None = None
    potency: int = 30
    potency_type: RadiCopenPotencyType = "C"
    use_adaptive_fibonacci: bool = True


def normalize_word(word: str) -> str:
    normalized = word.upper().strip()
    replacements = {"Ä": "AE", "Ö": "OE", "Ü": "UE", "ß": "SS"}
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    normalized = re.sub(r"\s*[DCLMF]+\d+", "", normalized)
    normalized = re.sub(r"[^A-Z0-9]", "", normalized)
    return normalized.strip()


def _char_value(char: str) -> int:
    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 1
    if "0" <= char <= "9":
        return int(char)
    return 0


def _primary_sum(normalized: str) -> int:
    return sum(_char_value(char) * index for index, char in enumerate(normalized, start=1))


def _adaptive_fibonacci_pairs(word_length: int) -> tuple[int, int]:
    """Return adaptive Fibonacci divider/multiplier pairs for Copen V4."""
    if word_length <= 0:
        return 21, 34
    if word_length <= 4:
        return 13, 21
    if word_length <= 10:
        return 21, 34
    if word_length <= 20:
        return 34, 55
    return 55, 89


def _potency_bonus(fibonacci_rate: int, potency: int, potency_type: RadiCopenPotencyType) -> int:
    factors = {
        "D": potency / 10.0,
        "C": potency / 5.0,
        "LM": potency / 2.0,
        "M": float(potency),
        "F1": potency / 6.0,
        "F2": potency / 4.0,
        "F3": potency / 3.0,
    }
    return math.floor(fibonacci_rate * factors[potency_type])


def _kozyrev_stub(seed: int | None) -> float:
    entropy = os.urandom(2)
    value = int.from_bytes(entropy, "big") if seed is None else seed % 65536
    return round(1.0 + (((value % 201) - 100) / 10000.0), 4)


def generate_rate_data(
    *,
    word: str,
    potency: int = 30,
    potency_type: RadiCopenPotencyType = "C",
    use_adaptive_fibonacci: bool = True,
    image_signature: str | None = None,
    kozyrev_factor: float = 1.0,
) -> RadiCopenRateData:
    """Generate Copen V4 rate data using weighted A=1..26 character sums."""
    normalized = normalize_word(word)
    if not normalized:
        raise ValueError("word_required_after_normalization")
    primary = _primary_sum(normalized)
    if image_signature:
        image_normalized = normalize_word(image_signature)
        if image_normalized:
            primary = (primary + _primary_sum(image_normalized)) // 2
    base_rate = primary * 1000
    div, mult = _adaptive_fibonacci_pairs(len(normalized)) if use_adaptive_fibonacci else (21, 34)
    fibonacci_rate = math.floor((base_rate / div) * mult)
    bonus = _potency_bonus(fibonacci_rate, potency, potency_type)
    final_rate = max(1, math.floor((fibonacci_rate + bonus) * kozyrev_factor))
    return RadiCopenRateData(
        word=word,
        normalized=normalized,
        primary_sum=primary,
        base_rate=base_rate,
        fibonacci_pair=f"{div}/{mult}",
        fibonacci_rate=fibonacci_rate,
        potency=f"{potency_type}{potency}",
        potency_bonus=bonus,
        final_rate=final_rate,
        kozyrev_influence=kozyrev_factor,
    )


def calculate_level_resonance(*, copen_rate: float, word: str) -> RadiCopenLevelResonance:
    """Calculate 13-level Copen V4 resonance for a final Copen rate."""
    normalized_word = normalize_word(word).lower()
    level_rows: list[RadiCopenLevelData] = []
    highest_level = 1
    highest_value = 0.0
    highest_name = str(LEVELS[0]["name"])
    for level in LEVELS:
        level_id = int(level["id"])
        min_freq = float(level["frequency_min"])
        max_freq = float(level["frequency_max"])
        if min_freq <= copen_rate <= max_freq:
            midpoint = (min_freq + max_freq) / 2.0
            distance = abs(copen_rate - midpoint)
            base = max(0.0, 100.0 - (distance / ((max_freq - min_freq) / 2.0)) * 50.0)
        elif copen_rate < min_freq:
            base = max(0.0, (copen_rate / min_freq) * 40.0)
        else:
            overshoot = (copen_rate - max_freq) / max_freq
            base = max(0.0, 30.0 - overshoot * 30.0)
        keywords = tuple(str(keyword) for keyword in level["keywords"])  # type: ignore[union-attr]
        keyword_bonus = sum(25.0 for keyword in keywords if keyword in normalized_word)
        resonance = min(100.0, base + keyword_bonus)
        name = str(level["name"])
        level_rows.append(
            RadiCopenLevelData(
                level_id=level_id,
                value=round(resonance, 2),
                name=name,
                description=str(level["description"]),
            )
        )
        if resonance > highest_value:
            highest_value = resonance
            highest_level = level_id
            highest_name = name
    return RadiCopenLevelResonance(
        levels=level_rows,
        highest_level=highest_level,
        highest_level_value=round(highest_value, 2),
        highest_level_name=highest_name,
    )


def _deterministic_float(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16) / float(2**256 - 1)


def _level_distribution(seed: str, draws: int = 100) -> dict[int, int]:
    distribution = {index: 0 for index in range(1, 14)}
    for draw in range(draws):
        value = _deterministic_float(f"{seed}:{draw}") * TOTAL_LEVEL_WEIGHT
        cumulative = 0
        for level in LEVELS:
            cumulative += int(level["weight"])
            if value < cumulative:
                distribution[int(level["id"])] += 1
                break
    return distribution


class RadiCopenEngine:
    """Execute RadiCopen Copen V4 rate analysis on the CPU."""

    def __init__(self, *, seed: int | None = None) -> None:
        self.seed = seed

    def execute(self, payload: RadiCopenExecutionInput) -> RadiCopenResultPayload:
        """Run a CPU-only RadiCopen full analysis."""
        word = payload.word or f"{payload.client_display_name} {payload.goal_title}".strip()
        kozyrev_factor = _kozyrev_stub(self.seed)
        image_signature = payload.client_code if payload.client_code else None
        rate = generate_rate_data(
            word=word,
            potency=payload.potency,
            potency_type=payload.potency_type,
            use_adaptive_fibonacci=payload.use_adaptive_fibonacci,
            image_signature=image_signature,
            kozyrev_factor=kozyrev_factor,
        )
        resonance = calculate_level_resonance(copen_rate=rate.final_rate, word=word)
        distribution = _level_distribution(word)
        dominant_level = max(distribution, key=distribution.get)
        return RadiCopenResultPayload(
            module_run_id=payload.module_run_id,
            tenant_id=payload.tenant_id,
            client_id=payload.client_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            manifest_version=payload.manifest_version,
            rate=rate,
            level_resonance=resonance,
            dominant_level=dominant_level,
            dominant_level_name=str(LEVELS[dominant_level - 1]["name"]),
            level_distribution=distribution,
        )
