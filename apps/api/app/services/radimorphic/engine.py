"""RadiMorphic CPU-only Hadamard/NLS engine."""

from __future__ import annotations

import hashlib
import math
import os
import random
from dataclasses import dataclass
from uuid import UUID

import numpy as np

from app.schemas.radimorphic import (
    RadiMorphicMultiplexScore,
    RadiMorphicNlsProfileInput,
    RadiMorphicResonance,
    RadiMorphicResultPayload,
    RadiMorphicScanMetrics,
)

VECTOR_DIMENSION = 128
DEFAULT_TOP_K = 8


@dataclass(frozen=True)
class RadiMorphicExecutionInput:
    """Tenant-scoped execution context for a RadiMorphic queued job."""

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
    nls_profiles: tuple[RadiMorphicNlsProfileInput, ...] | None = None


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        return vector
    return vector / norm


def _gpu_cuda_enabled() -> bool:
    _gpu_flag = os.getenv("RQ5_KOZYREV_GPU", "false").strip().lower()
    return False


def _next_power_of_two(size: int) -> int:
    if size < 1:
        raise ValueError("hadamard_size_must_be_positive")
    return 1 << (size - 1).bit_length()


def build_hadamard_s_matrix(size: int) -> np.ndarray:
    """Build a Sylvester Hadamard S-matrix with power-of-two padding."""
    padded = _next_power_of_two(size)
    matrix = np.array([[1.0]], dtype=np.float64)
    while matrix.shape[0] < padded:
        matrix = np.block([[matrix, matrix], [matrix, -matrix]])
    return matrix


def _hash_vector(text: str, *, dimension: int = VECTOR_DIMENSION) -> np.ndarray:
    values: list[float] = []
    counter = 0
    while len(values) < dimension:
        digest = hashlib.sha256(f"{text}:{counter}".encode()).digest()
        for byte in digest:
            values.append((byte / 127.5) - 1.0)
            if len(values) == dimension:
                break
        counter += 1
    return _normalize(np.array(values, dtype=np.float64))


def encode_client_signature(
    *,
    goal_title: str,
    goal_description: str,
    client_display_name: str,
    client_code: str | None = None,
) -> np.ndarray:
    """Encode the client/session context into a deterministic NLS signature."""
    text = "|".join(
        [
            goal_title.strip().lower(),
            goal_description.strip().lower(),
            client_display_name.strip().lower(),
            (client_code or "").strip().lower(),
        ]
    )
    return _hash_vector(text)


def encode_nls_profile(profile: RadiMorphicNlsProfileInput) -> np.ndarray:
    """Encode one NLS profile into the shared Hadamard vector space."""
    base = _hash_vector(
        "|".join(
            [
                profile.item_id.lower(),
                profile.name.lower(),
                profile.category.lower(),
                f"{profile.frequency_hz:.6f}",
                profile.description or "",
            ]
        )
    )
    harmonic = np.zeros(VECTOR_DIMENSION, dtype=np.float64)
    frequency = max(profile.frequency_hz, 0.0)
    for index in range(VECTOR_DIMENSION):
        phase = (index + 1) * frequency / 1000.0
        harmonic[index] = math.sin(phase) + 0.5 * math.cos(phase / 2.0)
    for index, rate in enumerate(profile.rates[:24]):
        harmonic[index % VECTOR_DIMENSION] += float(rate) / 1000.0
    harmonic = _normalize(harmonic)
    return _normalize((base * 0.72) + (harmonic * 0.28))


def encode_nls_profiles(profiles: list[RadiMorphicNlsProfileInput]) -> np.ndarray:
    """Encode NLS profile inputs into a matrix of normalized profile vectors."""
    if not profiles:
        raise ValueError("nls_profiles_required")
    return np.vstack([encode_nls_profile(profile) for profile in profiles])


def _hadamard_multiplex(client_signature: np.ndarray, nls_profiles: np.ndarray) -> np.ndarray:
    """Apply the CPU-only Hadamard S-matrix multiplex transform."""
    signature = np.asarray(client_signature, dtype=np.float64)
    profiles = np.asarray(nls_profiles, dtype=np.float64)
    if signature.ndim != 1:
        raise ValueError("client_signature_must_be_vector")
    if profiles.ndim != 2:
        raise ValueError("nls_profiles_must_be_matrix")
    if profiles.shape[1] != signature.shape[0]:
        raise ValueError("profile_dimension_mismatch")

    hadamard_size = _next_power_of_two(signature.shape[0])
    hadamard = build_hadamard_s_matrix(hadamard_size) / math.sqrt(hadamard_size)
    padded_signature = np.zeros(hadamard_size, dtype=np.float64)
    padded_profiles = np.zeros((profiles.shape[0], hadamard_size), dtype=np.float64)
    padded_signature[: signature.shape[0]] = signature
    padded_profiles[:, : profiles.shape[1]] = profiles
    transformed_signature = hadamard @ padded_signature
    transformed_profiles = padded_profiles @ hadamard.T
    return np.abs(transformed_profiles @ transformed_signature)


def multiplex_scan(
    *,
    client_signature: np.ndarray,
    nls_profiles: np.ndarray,
    top_k: int = DEFAULT_TOP_K,
    use_hadamard: bool = True,
) -> list[RadiMorphicMultiplexScore]:
    """Rank NLS profiles by Hadamard multiplex resonance."""
    profiles = np.asarray(nls_profiles, dtype=np.float64)
    if profiles.ndim != 2 or profiles.shape[0] == 0:
        raise ValueError("nls_profiles_required")
    if top_k < 1:
        raise ValueError("top_k_must_be_positive")

    raw_scores = (
        _hadamard_multiplex(client_signature, profiles)
        if use_hadamard
        else np.abs(profiles @ np.asarray(client_signature, dtype=np.float64))
    )
    raw_scores = np.clip(raw_scores, 0.0, None)
    max_score = float(np.max(raw_scores)) or 1.0
    normalized = np.clip(raw_scores / max_score, 0.0, 1.0)
    order = np.argsort(normalized)[::-1][: min(top_k, profiles.shape[0])]
    return [
        RadiMorphicMultiplexScore(
            profile_index=int(index),
            resonance_score=float(normalized[index]),
            raw_score=float(raw_scores[index]),
        )
        for index in order
    ]


def nls_profile_resonance(
    *,
    profiles: list[RadiMorphicNlsProfileInput],
    client_signature: np.ndarray,
    top_k: int = DEFAULT_TOP_K,
) -> list[RadiMorphicResonance]:
    """Build ranked NLS profile resonance scores."""
    matrix = encode_nls_profiles(profiles)
    scores = multiplex_scan(client_signature=client_signature, nls_profiles=matrix, top_k=top_k)
    resonances: list[RadiMorphicResonance] = []
    for rank, score in enumerate(scores, start=1):
        profile = profiles[score.profile_index]
        resonances.append(
            RadiMorphicResonance(
                item_id=profile.item_id,
                name=profile.name,
                category=profile.category,
                frequency_hz=profile.frequency_hz,
                resonance_score=score.resonance_score,
                rank=rank,
            )
        )
    return resonances


def _scan_metrics(scores: list[RadiMorphicMultiplexScore]) -> RadiMorphicScanMetrics:
    values = np.array([score.resonance_score for score in scores], dtype=np.float64)
    if values.size == 0:
        raise ValueError("scores_required")
    probabilities = values / (float(np.sum(values)) or 1.0)
    nonzero = probabilities[probabilities > 0]
    entropy = -float(np.sum(nonzero * np.log2(nonzero)))
    max_entropy = math.log2(values.size) if values.size > 1 else 1.0
    quality_score = float(np.clip(np.mean(values[: min(3, values.size)]), 0.0, 1.0))
    morphic_field = float(np.clip((np.max(values) * 0.65) + (np.mean(values) * 0.35), 0.0, 1.0))
    return RadiMorphicScanMetrics(
        quality_score=quality_score,
        morphic_field=morphic_field,
        holographic_entropy=float(np.clip(entropy / max_entropy, 0.0, 1.0)),
    )


def _default_profiles(seed: int) -> list[RadiMorphicNlsProfileInput]:
    names = [
        ("cellular coherence", "coherence", 432.0),
        ("hydration field", "wellbeing", 528.0),
        ("autonomic balance", "regulation", 639.0),
        ("sleep recovery", "recovery", 741.0),
        ("focus clarity", "cognition", 852.0),
        ("grounded vitality", "vitality", 963.0),
        ("emotional steadiness", "affect", 396.0),
        ("integration tone", "integration", 417.0),
        ("breath rhythm", "regulation", 174.0),
        ("session alignment", "coherence", 285.0),
    ]
    rng = random.Random(seed)
    profiles: list[RadiMorphicNlsProfileInput] = []
    for index, (name, category, frequency) in enumerate(names):
        rates = [round(rng.uniform(20.0, 980.0), 4) for _ in range(5)]
        profiles.append(
            RadiMorphicNlsProfileInput(
                item_id=f"nls-{index + 1:03d}",
                name=name,
                category=category,
                frequency_hz=frequency,
                rates=rates,
                description=f"Non-medical wellbeing NLS profile for {category}.",
            )
        )
    return profiles


class RadiMorphicEngine:
    """Execute RadiMorphic Hadamard/NLS scoring on the CPU."""

    def __init__(self, *, seed: int | None = None) -> None:
        self.seed = seed

    def execute(self, payload: RadiMorphicExecutionInput) -> RadiMorphicResultPayload:
        """Run a CPU-only RadiMorphic scan and return a validated result payload."""
        entropy_bytes = os.urandom(16)
        entropy_seed = int.from_bytes(entropy_bytes, "big")
        seed = self.seed if self.seed is not None else entropy_seed
        profiles = list(payload.nls_profiles or _default_profiles(seed))
        client_signature = encode_client_signature(
            goal_title=payload.goal_title,
            goal_description=payload.goal_description,
            client_display_name=payload.client_display_name,
            client_code=payload.client_code,
        )
        matrix = encode_nls_profiles(profiles)
        all_scores = multiplex_scan(
            client_signature=client_signature,
            nls_profiles=matrix,
            top_k=len(profiles),
        )
        top_resonances = nls_profile_resonance(
            profiles=profiles,
            client_signature=client_signature,
            top_k=DEFAULT_TOP_K,
        )
        return RadiMorphicResultPayload(
            module_run_id=payload.module_run_id,
            tenant_id=payload.tenant_id,
            client_id=payload.client_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            manifest_version=payload.manifest_version,
            gpu_cuda_execution_enabled=_gpu_cuda_enabled(),
            matrix_shape=(int(matrix.shape[0]), int(matrix.shape[1])),
            top_resonances=top_resonances,
            metrics=_scan_metrics(all_scores),
            total_profiles=len(profiles),
        )
