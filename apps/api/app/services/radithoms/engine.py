"""RadiThoms CPU-only 5D vector and meridian engine."""

from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass
from uuid import UUID

import numpy as np

from app.schemas.radithoms import (
    RadiThomsAcupuncturePoint,
    RadiThomsAttractorProfile,
    RadiThomsClientVector5D,
    RadiThomsElement,
    RadiThomsMeridianBalance,
    RadiThomsResultPayload,
)

TCM_MERIDIANS: tuple[tuple[str, RadiThomsElement, str], ...] = (
    ("lung", "metal", "yin"),
    ("large_intestine", "metal", "yang"),
    ("stomach", "earth", "yang"),
    ("spleen", "earth", "yin"),
    ("heart", "fire", "yin"),
    ("small_intestine", "fire", "yang"),
    ("bladder", "water", "yang"),
    ("kidney", "water", "yin"),
    ("pericardium", "fire", "yin"),
    ("triple_warmer", "fire", "yang"),
    ("gallbladder", "wood", "yang"),
    ("liver", "wood", "yin"),
)
ACUPUNCTURE_POINTS: tuple[tuple[str, str, str, float, str], ...] = (
    ("LU-7", "Lieque", "lung", 7.83, "wrist"),
    ("LI-4", "Hegu", "large_intestine", 10.0, "hand"),
    ("ST-36", "Zusanli", "stomach", 12.0, "lower_leg"),
    ("SP-6", "Sanyinjiao", "spleen", 8.0, "lower_leg"),
    ("HT-7", "Shenmen", "heart", 7.5, "wrist"),
    ("SI-3", "Houxi", "small_intestine", 9.0, "hand"),
    ("BL-23", "Shenshu", "bladder", 6.0, "back"),
    ("KI-3", "Taixi", "kidney", 5.5, "foot"),
    ("PC-6", "Neiguan", "pericardium", 7.0, "forearm"),
    ("TE-5", "Waiguan", "triple_warmer", 8.5, "forearm"),
    ("GB-34", "Yanglingquan", "gallbladder", 11.0, "lower_leg"),
    ("LR-3", "Taichong", "liver", 9.5, "foot"),
)
ATTRACTORS = (
    "health",
    "balance",
    "regeneration",
    "transformation",
    "stability",
    "growth",
    "integration",
    "harmony",
)


@dataclass(frozen=True)
class RadiThomsExecutionInput:
    """Tenant-scoped execution context for a RadiThoms queued job."""

    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    goal_title: str
    goal_description: str
    client_display_name: str
    client_code: str | None = None
    birth_date: str = "1980-01-15"
    manifest_version: str = "1.0.0"


def _clamp01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _field_signature(
    *,
    client_name: str,
    birth_date: str,
    birth_place: str | None,
    seed: int,
) -> str:
    payload = f"{client_name}:{birth_date}:{birth_place or 'unknown'}:{seed}:stub"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _calculate_client_vector(
    *,
    client_name: str,
    birth_date: str,
    signature: str,
    resonance_score: float | None = None,
) -> RadiThomsClientVector5D:
    """Calculate a bounded 5D client vector (x/y/z/w/t)."""
    seed = int(signature[:8], 16)
    year, month, day = [int(part) for part in birth_date.split("-")]
    life_phase = _clamp01((2026 - year) / 100.0)
    name_value = sum(ord(char) for char in client_name.lower()) / 1000.0
    x = math.sin(seed * 0.001 + name_value) * 0.5 + 0.5
    y = math.cos(seed * 0.002 + month / 12.0) * 0.5 + 0.5
    z = math.sin(seed * 0.003 + day / 31.0) * 0.5 + 0.5
    w = math.cos(seed * 0.004 + name_value) * 0.5 + 0.5
    t = life_phase
    if resonance_score is not None:
        resonance = max(-0.15, min(0.15, resonance_score * 0.1))
        x = _clamp01(x + resonance)
        y = _clamp01(y + resonance / 2.0)
        z = _clamp01(z + resonance / 3.0)
    return RadiThomsClientVector5D(
        x=round(_clamp01(x), 4),
        y=round(_clamp01(y), 4),
        z=round(_clamp01(z), 4),
        w=round(_clamp01(w), 4),
        t=round(_clamp01(t), 4),
    )


def _analyze_meridians(vector: RadiThomsClientVector5D) -> list[RadiThomsMeridianBalance]:
    dimensions = [vector.x, vector.y, vector.z, vector.w, vector.t]
    balances: list[RadiThomsMeridianBalance] = []
    for index, (name, element, yin_yang) in enumerate(TCM_MERIDIANS):
        component = dimensions[index % len(dimensions)]
        offset = (index * 0.1) % 1.0
        balance = math.sin((component + offset) * math.tau) * 0.8
        energy_level = round(_clamp01(1.0 - abs(balance)) * 100.0, 1)
        balances.append(
            RadiThomsMeridianBalance(
                meridian_name=name,
                element=element,
                yin_yang=yin_yang,  # type: ignore[arg-type]
                balance_score=round(balance, 3),
                energy_level=energy_level,
            )
        )
    return balances


def _dominant_element(balances: list[RadiThomsMeridianBalance]) -> RadiThomsElement:
    scores: dict[str, float] = {}
    for balance in balances:
        scores[balance.element] = scores.get(balance.element, 0.0) + abs(balance.balance_score)
    return max(scores, key=scores.get)  # type: ignore[return-value]


def _recommend_acupuncture_points(
    balances: list[RadiThomsMeridianBalance],
    *,
    count: int = 5,
) -> list[RadiThomsAcupuncturePoint]:
    sorted_balances = sorted(balances, key=lambda balance: balance.balance_score)
    recommendations: list[RadiThomsAcupuncturePoint] = []
    for balance in sorted_balances[:count]:
        for point_id, name, meridian, frequency, location in ACUPUNCTURE_POINTS:
            if meridian == balance.meridian_name:
                recommendations.append(
                    RadiThomsAcupuncturePoint(
                        point_id=point_id,
                        name=name,
                        meridian=meridian,
                        frequency_hz=frequency,
                        location=location,
                        activation_score=round(min(1.0, abs(balance.balance_score)), 3),
                    )
                )
                break
    return recommendations


def _catastrophe_attractors(vector: RadiThomsClientVector5D) -> RadiThomsAttractorProfile:
    """Calculate catastrophe-theory attractor, stability, and transition risk."""
    dimensions = np.array([vector.x, vector.y, vector.z, vector.w, vector.t], dtype=np.float64)
    phi_weights = np.array([1.0, 1.618, 2.618, 4.236, 6.854], dtype=np.float64)
    weighted = dimensions * (phi_weights / float(np.sum(phi_weights)))
    mixer = np.eye(5, dtype=np.float64) * 0.72
    mixer += (np.ones((5, 5), dtype=np.float64) - np.eye(5, dtype=np.float64)) * 0.07
    optimized = mixer @ weighted
    norm = float(np.linalg.norm(optimized)) or 1.0
    optimized = np.clip(optimized / norm, 0.0, 1.0)
    attractor_index = int(np.argmax(optimized)) % len(ATTRACTORS)
    magnitude = float(np.linalg.norm(dimensions))
    stability = _clamp01((magnitude / math.sqrt(5.0)) * 0.72 + float(np.max(optimized)) * 0.28)
    return RadiThomsAttractorProfile(
        current_attractor=ATTRACTORS[attractor_index],
        attractor_stability=round(stability, 3),
        catastrophe_risk=round(1.0 - stability, 3),
    )


class RadiThomsEngine:
    """Execute RadiThoms 5D meridian analysis on the CPU."""

    def __init__(self, *, seed: int | None = None) -> None:
        self.seed = seed

    def analyze(self, payload: RadiThomsExecutionInput) -> RadiThomsResultPayload:
        """Run a CPU-only RadiThoms meridian analysis."""
        entropy_bytes = os.urandom(16)
        entropy_seed = int.from_bytes(entropy_bytes, "big")
        seed = self.seed if self.seed is not None else entropy_seed
        signature = _field_signature(
            client_name=payload.client_display_name,
            birth_date=payload.birth_date,
            birth_place=payload.client_code,
            seed=seed,
        )
        text_score = (len(payload.goal_title) + len(payload.goal_description)) / 100.0
        vector = _calculate_client_vector(
            client_name=payload.client_display_name,
            birth_date=payload.birth_date,
            signature=signature,
            resonance_score=text_score,
        )
        balances = _analyze_meridians(vector)
        points = _recommend_acupuncture_points(balances)
        attractor = _catastrophe_attractors(vector)
        primary_frequency = round(7.83 * (1.0 + vector.x * 0.5), 2)
        harmonics = [point.frequency_hz for point in points]
        return RadiThomsResultPayload(
            module_run_id=payload.module_run_id,
            tenant_id=payload.tenant_id,
            client_id=payload.client_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            manifest_version=payload.manifest_version,
            field_signature=signature,
            client_vector=vector,
            meridian_balances=balances,
            dominant_element=_dominant_element(balances),
            recommended_points=points,
            attractor=attractor,
            primary_frequency_hz=primary_frequency,
            harmonic_frequencies=harmonics,
        )

    def execute(self, payload: RadiThomsExecutionInput) -> RadiThomsResultPayload:
        """Run the worker-facing RadiThoms analysis entry point."""
        return self.analyze(payload)
