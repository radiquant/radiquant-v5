"""RadiBlohm CPU-only morphic field engine."""

from __future__ import annotations

import hashlib
import math
import os
import random
from dataclasses import dataclass
from uuid import UUID

import numpy as np

from app.schemas.radiblohm import (
    RadiBlohmGeometry,
    RadiBlohmGeometryProfile,
    RadiBlohmMorphicField,
    RadiBlohmResultPayload,
    RadiBlohmSuperpositionTerm,
    RadiBlohmTcmElement,
    RadiBlohmTcmProfile,
)

HBAR = 1.054571817e-34
GEOMETRIC_FACTORS: dict[str, float] = {
    "tetrahedron": 1.618,
    "cube": 1.732,
    "octahedron": 2.000,
    "dodecahedron": 2.618,
    "icosahedron": 2.236,
    "flower_of_life": 2.718,
}
TCM_ELEMENT_FACTORS: dict[str, float] = {
    "holz": 1.272,
    "feuer": 1.618,
    "erde": 1.000,
    "metall": 1.414,
    "wasser": 1.155,
}
TCM_ELEMENT_FREQUENCIES: dict[str, float] = {
    "holz": 317.83,
    "feuer": 395.25,
    "erde": 264.00,
    "metall": 281.00,
    "wasser": 352.00,
}
TCM_SHENG_CYCLE: dict[str, str] = {
    "holz": "feuer",
    "feuer": "erde",
    "erde": "metall",
    "metall": "wasser",
    "wasser": "holz",
}
TCM_KE_CYCLE: dict[str, str] = {
    "holz": "erde",
    "erde": "wasser",
    "wasser": "feuer",
    "feuer": "metall",
    "metall": "holz",
}


@dataclass(frozen=True)
class RadiBlohmExecutionInput:
    """Tenant-scoped execution context for a RadiBlohm queued job."""

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
    geometric_form: RadiBlohmGeometry = "flower_of_life"
    tcm_element: RadiBlohmTcmElement = "erde"


def _numerical_factor(text: str) -> float:
    total = sum(ord(char) * (index + 1) for index, char in enumerate(text.lower()))
    return max(0.1, min(10.0, ((total % 1000) / 100.0) + 0.1))


def _coherence(values: list[float]) -> float:
    array = np.array(values, dtype=np.float64)
    variance = float(np.var(array))
    return float(np.clip(math.exp(-min(variance / (math.pi**2), 100.0)), 0.0, 1.0))


def calculate_morphic_field(
    *,
    time_value: float,
    amplitudes: np.ndarray | None = None,
    energies: np.ndarray | None = None,
) -> tuple[float, list[RadiBlohmSuperpositionTerm]]:
    """Calculate quantum superposition psi = sum a_n * cos(E_n * t / hbar)."""
    amp = np.asarray(amplitudes if amplitudes is not None else np.full(5, 1 / math.sqrt(5)))
    energy = np.asarray(energies if energies is not None else np.arange(1, amp.size + 1))
    if amp.ndim != 1 or energy.ndim != 1 or amp.size != energy.size or amp.size == 0:
        raise ValueError("matching_quantum_states_required")

    phase = np.remainder((energy * time_value) / HBAR, 2 * math.pi)
    contributions = amp * np.cos(phase)
    amplitude_sum = max(float(np.sum(np.abs(amp))), 1.0)
    psi = float(np.clip(abs(np.sum(contributions)) / amplitude_sum, 0.0, 1.0))
    terms = [
        RadiBlohmSuperpositionTerm(
            state_index=index + 1,
            amplitude=float(amp[index]),
            energy=float(energy[index]),
            contribution=float(contributions[index]),
        )
        for index in range(amp.size)
    ]
    return psi, terms


def _apply_platonic_geometry(
    psi_value: float,
    geometric_form: RadiBlohmGeometry,
) -> tuple[float, RadiBlohmGeometryProfile]:
    """Apply Platonic geometry modulation to the morphic field."""
    factor = GEOMETRIC_FACTORS.get(geometric_form, 1.0)
    modulation = float(np.clip(math.tanh(factor / 3.0), 0.0, 1.0))
    return psi_value * factor * modulation, RadiBlohmGeometryProfile(
        form=geometric_form,
        factor=factor,
        modulation=modulation,
    )


def _apply_tcm_elements(
    value: float,
    element: RadiBlohmTcmElement,
) -> tuple[float, RadiBlohmTcmProfile]:
    """Apply TCM element modulation using Sheng and Ke cycle relations."""
    factor = TCM_ELEMENT_FACTORS.get(element, 1.0)
    nourishing = TCM_SHENG_CYCLE.get(element, "erde")
    controlling = TCM_KE_CYCLE.get(element, "erde")
    sheng_boost = TCM_ELEMENT_FACTORS.get(nourishing, 1.0) * 0.05
    ke_balance = TCM_ELEMENT_FACTORS.get(controlling, 1.0) * 0.03
    combined = factor + sheng_boost - ke_balance
    modulation = float(np.clip(math.tanh(combined / 2.0), 0.0, 1.0))
    return value * combined * modulation, RadiBlohmTcmProfile(
        element=element,
        factor=combined,
        nourishing_element=nourishing,  # type: ignore[arg-type]
        controlling_element=controlling,  # type: ignore[arg-type]
        modulation=modulation,
    )


def _derive_shape_inputs(seed: int, text: str) -> tuple[RadiBlohmGeometry, RadiBlohmTcmElement]:
    digest = hashlib.sha256(f"{seed}:{text}".encode()).digest()
    geometry = list(GEOMETRIC_FACTORS.keys())[digest[0] % len(GEOMETRIC_FACTORS)]
    element = list(TCM_ELEMENT_FACTORS.keys())[digest[1] % len(TCM_ELEMENT_FACTORS)]
    return geometry, element  # type: ignore[return-value]


class RadiBlohmEngine:
    """Execute RadiBlohm morphic field scoring on the CPU."""

    def __init__(self, *, seed: int | None = None) -> None:
        self.seed = seed

    def execute(self, payload: RadiBlohmExecutionInput) -> RadiBlohmResultPayload:
        """Run a CPU-only RadiBlohm morphic field calculation."""
        entropy_bytes = os.urandom(16)
        entropy_seed = int.from_bytes(entropy_bytes, "big")
        seed = self.seed if self.seed is not None else entropy_seed
        text = "|".join(
            [
                payload.goal_title.strip().lower(),
                payload.goal_description.strip().lower(),
                payload.client_display_name.strip().lower(),
                (payload.client_code or "").strip().lower(),
            ]
        )
        derived_geometry, derived_element = _derive_shape_inputs(seed, text)
        geometric_form = payload.geometric_form or derived_geometry
        tcm_element = payload.tcm_element or derived_element
        rng = random.Random(seed)
        time_value = rng.uniform(0.001, 0.999)
        amplitudes = np.array([rng.uniform(0.2, 1.0) for _ in range(5)], dtype=np.float64)
        amplitudes = amplitudes / max(float(np.linalg.norm(amplitudes)), 1.0)
        energies = np.array([float(index + 1) for index in range(5)], dtype=np.float64)
        quantum_component, terms = calculate_morphic_field(
            time_value=time_value,
            amplitudes=amplitudes,
            energies=energies,
        )
        numerical = _numerical_factor(text)
        geometric_value, geometry = _apply_platonic_geometry(quantum_component, geometric_form)
        tcm_value, tcm = _apply_tcm_elements(geometric_value * numerical, tcm_element)
        normalized = float(np.clip(math.tanh(tcm_value / 25.0), 0.0, 1.0))
        coherence = _coherence(
            [quantum_component, numerical / 10.0, geometry.modulation, tcm.modulation]
        )
        field_strength = float(np.clip(normalized * coherence, 0.0, 1.0))
        resonance_frequency = TCM_ELEMENT_FREQUENCIES[tcm.element] * max(numerical / 10.0, 0.1)
        return RadiBlohmResultPayload(
            module_run_id=payload.module_run_id,
            tenant_id=payload.tenant_id,
            client_id=payload.client_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            manifest_version=payload.manifest_version,
            morphic_field=RadiBlohmMorphicField(
                psi_total=normalized,
                quantum_component=quantum_component,
                numerical_factor=numerical,
                geometric_factor=geometry.factor,
                tcm_factor=tcm.factor,
                field_strength=field_strength,
                coherence=coherence,
                resonance_frequency=resonance_frequency,
            ),
            geometry=geometry,
            tcm=tcm,
            superposition_terms=terms,
        )
