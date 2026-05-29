"""Pure Radi144 domain service primitives.

Radi144 Domain Service Gate scope: deterministic, unit-testable core functions
for vectorization, 12x12 resonance matrix construction, normalization,
confidence and synergy seed calculation. This module intentionally has no DB,
FastAPI, worker, event writer, persistence, GPU, or route dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import sqrt
from typing import Final

VECTOR_DIMENSIONS: Final[int] = 256
MATRIX_SIZE: Final[int] = 12
DEFAULT_REFERENCE_LABELS: Final[tuple[str, ...]] = (
    "grounding",
    "breath",
    "rhythm",
    "focus",
    "clarity",
    "balance",
    "warmth",
    "flow",
    "rest",
    "integration",
    "resilience",
    "reflection",
)


class Radi144DomainError(ValueError):
    """Raised when Radi144 pure-domain inputs are invalid."""


@dataclass(frozen=True)
class Radi144InputContext:
    """Minimal tenant-safe context needed to build the Radi144 input vector."""

    tenant_id: str
    client_id: str
    session_id: str
    goal_title: str
    goal_description: str = ""
    client_display_name: str = ""
    client_code: str | None = None
    consent_purpose: str = "analysis"


@dataclass(frozen=True)
class Radi144ReferenceVector:
    """Versioned reference vector used by the 12x12 resonance matrix."""

    id: str
    label: str
    values: tuple[float, ...]


@dataclass(frozen=True)
class Radi144ComputationPlan:
    """Pure domain output bundle; not a persisted ModuleResult."""

    client_vector: tuple[float, ...]
    reference_vectors: tuple[Radi144ReferenceVector, ...]
    raw_resonance_matrix: tuple[tuple[float, ...], ...]
    normalized_matrix: tuple[tuple[float, ...], ...]
    coherence_scores: dict[str, float]
    biofield_map: dict[str, float]
    confidence: dict[str, float | str]
    synergy_seed: dict[str, object]


class Radi144DomainService:
    """Deterministic Radi144 core calculations for unit-tested domain logic."""

    vector_dimensions = VECTOR_DIMENSIONS
    matrix_size = MATRIX_SIZE

    def build_plan(
        self,
        context: Radi144InputContext,
        reference_vectors: tuple[Radi144ReferenceVector, ...] | None = None,
    ) -> Radi144ComputationPlan:
        """Build a complete pure-domain computation plan without side effects."""
        references = reference_vectors or self.default_reference_vectors()
        client_vector = self.vectorize_client_context(context)
        raw_matrix = self.compute_resonance_matrix(client_vector, references)
        normalized_matrix = self.normalize_matrix(raw_matrix)
        coherence_scores = self.extract_coherence_scores(normalized_matrix, references)
        biofield_map = self.build_biofield_map(coherence_scores)
        confidence = self.assess_confidence(context=context, matrix=normalized_matrix)
        synergy_seed = self.create_synergy_seed(biofield_map=biofield_map, confidence=confidence, matrix=normalized_matrix)
        return Radi144ComputationPlan(
            client_vector=client_vector,
            reference_vectors=references,
            raw_resonance_matrix=raw_matrix,
            normalized_matrix=normalized_matrix,
            coherence_scores=coherence_scores,
            biofield_map=biofield_map,
            confidence=confidence,
            synergy_seed=synergy_seed,
        )

    def vectorize_client_context(self, context: Radi144InputContext) -> tuple[float, ...]:
        """Create a stable 256-dimensional normalized vector from safe context fields."""
        self._validate_context(context)
        text = "|".join(
            [
                context.tenant_id,
                context.client_id,
                context.session_id,
                context.goal_title,
                context.goal_description,
                context.client_display_name,
                context.client_code or "",
                context.consent_purpose,
            ]
        ).lower()
        vector = [0.0 for _ in range(self.vector_dimensions)]
        for token in self._tokens(text):
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.vector_dimensions
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            weight = 0.5 + (digest[3] / 255.0)
            vector[index] += sign * weight
        return self._normalize_vector(tuple(vector))

    def default_reference_vectors(self) -> tuple[Radi144ReferenceVector, ...]:
        """Create the default 12 reference vectors from stable Wellbeing labels."""
        return tuple(
            Radi144ReferenceVector(
                id=f"radi144.ref.{index + 1:02d}",
                label=label,
                values=self._reference_vector(label),
            )
            for index, label in enumerate(DEFAULT_REFERENCE_LABELS)
        )

    def compute_resonance_matrix(
        self,
        client_vector: tuple[float, ...],
        reference_vectors: tuple[Radi144ReferenceVector, ...],
    ) -> tuple[tuple[float, ...], ...]:
        """Compute a deterministic client-weighted 12x12 cosine resonance matrix."""
        self._validate_vector(client_vector, "client_vector")
        self._validate_references(reference_vectors)
        client_affinity = [self._cosine(client_vector, reference.values) for reference in reference_vectors]
        rows: list[tuple[float, ...]] = []
        for left_index, left in enumerate(reference_vectors):
            row: list[float] = []
            for right_index, right in enumerate(reference_vectors):
                reference_similarity = self._cosine(left.values, right.values)
                client_bridge = client_affinity[left_index] * client_affinity[right_index]
                value = (reference_similarity + client_bridge) / 2.0
                row.append(self._clamp(value))
            rows.append(tuple(row))
        return tuple(rows)

    def normalize_matrix(self, matrix: tuple[tuple[float, ...], ...]) -> tuple[tuple[float, ...], ...]:
        """Symmetrize and clamp a 12x12 matrix to stable -1..1 values."""
        self._validate_matrix(matrix)
        normalized: list[tuple[float, ...]] = []
        for row_index in range(self.matrix_size):
            row: list[float] = []
            for column_index in range(self.matrix_size):
                if row_index == column_index:
                    row.append(1.0)
                    continue
                value = (matrix[row_index][column_index] + matrix[column_index][row_index]) / 2.0
                row.append(round(self._clamp(value), 6))
            normalized.append(tuple(row))
        return tuple(normalized)

    def extract_coherence_scores(
        self,
        matrix: tuple[tuple[float, ...], ...],
        reference_vectors: tuple[Radi144ReferenceVector, ...],
    ) -> dict[str, float]:
        """Extract row-average coherence scores keyed by reference label."""
        self._validate_matrix(matrix)
        self._validate_references(reference_vectors)
        scores: dict[str, float] = {}
        for index, reference in enumerate(reference_vectors):
            row = matrix[index]
            off_diagonal = [abs(value) for column, value in enumerate(row) if column != index]
            scores[reference.label] = round(sum(off_diagonal) / len(off_diagonal), 6)
        return scores

    def build_biofield_map(self, coherence_scores: dict[str, float]) -> dict[str, float]:
        """Build a sorted, projection-safe Wellbeing map from coherence scores."""
        if set(coherence_scores) != set(DEFAULT_REFERENCE_LABELS):
            raise Radi144DomainError("coherence_scores must cover the default Radi144 labels")
        return dict(sorted(coherence_scores.items(), key=lambda item: (-item[1], item[0])))

    def assess_confidence(
        self,
        *,
        context: Radi144InputContext,
        matrix: tuple[tuple[float, ...], ...],
    ) -> dict[str, float | str]:
        """Assess data and matrix stability as non-medical quality metadata."""
        self._validate_context(context)
        self._validate_matrix(matrix)
        text_length = len(" ".join([context.goal_title, context.goal_description, context.client_display_name]).strip())
        data_quality = min(1.0, max(0.2, text_length / 160.0))
        off_diagonal = [abs(matrix[row][column]) for row in range(self.matrix_size) for column in range(self.matrix_size) if row != column]
        stability = 1.0 - min(0.8, self._variance(off_diagonal))
        score = round((data_quality * 0.55) + (stability * 0.45), 6)
        return {
            "score": score,
            "data_quality": round(data_quality, 6),
            "stability": round(stability, 6),
            "language_scope": "wellbeing_only",
        }

    def create_synergy_seed(
        self,
        *,
        biofield_map: dict[str, float],
        confidence: dict[str, float | str],
        matrix: tuple[tuple[float, ...], ...],
    ) -> dict[str, object]:
        """Create a compact handoff seed for later modules without raw matrix data."""
        self._validate_matrix(matrix)
        top_labels = list(biofield_map)[:3]
        checksum_source = ";".join(f"{label}:{biofield_map[label]:.6f}" for label in top_labels)
        checksum = sha256(checksum_source.encode("utf-8")).hexdigest()[:16]
        return {
            "source_module": "radi144",
            "top_labels": top_labels,
            "confidence_score": confidence["score"],
            "matrix_shape": [self.matrix_size, self.matrix_size],
            "seed_checksum": checksum,
        }

    def _reference_vector(self, label: str) -> tuple[float, ...]:
        values: list[float] = []
        counter = 0
        while len(values) < self.vector_dimensions:
            digest = sha256(f"radi144:{label}:{counter}".encode("utf-8")).digest()
            for byte in digest:
                values.append((byte / 127.5) - 1.0)
                if len(values) == self.vector_dimensions:
                    break
            counter += 1
        return self._normalize_vector(tuple(values))

    def _validate_context(self, context: Radi144InputContext) -> None:
        if context.consent_purpose != "analysis":
            raise Radi144DomainError("Radi144 requires active analysis consent")
        for field_name in ["tenant_id", "client_id", "session_id", "goal_title"]:
            if not getattr(context, field_name).strip():
                raise Radi144DomainError(f"{field_name} is required")

    def _validate_references(self, references: tuple[Radi144ReferenceVector, ...]) -> None:
        if len(references) != self.matrix_size:
            raise Radi144DomainError("Radi144 requires exactly 12 reference vectors")
        seen_ids: set[str] = set()
        for reference in references:
            if reference.id in seen_ids:
                raise Radi144DomainError("Radi144 reference IDs must be unique")
            seen_ids.add(reference.id)
            self._validate_vector(reference.values, f"reference_vector:{reference.id}")

    def _validate_vector(self, vector: tuple[float, ...], name: str) -> None:
        if len(vector) != self.vector_dimensions:
            raise Radi144DomainError(f"{name} must have {self.vector_dimensions} dimensions")
        if not any(value != 0.0 for value in vector):
            raise Radi144DomainError(f"{name} must not be all zeros")

    def _validate_matrix(self, matrix: tuple[tuple[float, ...], ...]) -> None:
        if len(matrix) != self.matrix_size or any(len(row) != self.matrix_size for row in matrix):
            raise Radi144DomainError("Radi144 matrix must be 12x12")

    def _normalize_vector(self, vector: tuple[float, ...]) -> tuple[float, ...]:
        magnitude = sqrt(sum(value * value for value in vector))
        if magnitude == 0.0:
            raise Radi144DomainError("Cannot normalize an empty vector")
        return tuple(round(value / magnitude, 9) for value in vector)

    def _cosine(self, left: tuple[float, ...], right: tuple[float, ...]) -> float:
        self._validate_vector(left, "left")
        self._validate_vector(right, "right")
        return self._clamp(sum(left[index] * right[index] for index in range(self.vector_dimensions)))

    def _clamp(self, value: float) -> float:
        return max(-1.0, min(1.0, value))

    def _tokens(self, text: str) -> list[str]:
        tokens = [token.strip() for token in text.replace("|", " ").split() if token.strip()]
        return tokens or ["radi144-empty-context"]

    def _variance(self, values: list[float]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((value - mean) ** 2 for value in values) / len(values)
