"""Radi144 deterministic CPU-safe execution service.

CPU Safe Execution Gate scope: build a validated Radi144Result DTO from the
pure domain service without database writes, worker wiring, or projection writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from app.schemas.radi144_result import (
    Radi144ClientProjectionPlaceholder,
    Radi144Confidence,
    Radi144Provenance,
    Radi144Result,
    Radi144Retention,
    Radi144SynergySeed,
)
from app.services.radi144.domain import Radi144DomainService, Radi144InputContext

ALGORITHM_VERSION = "radi144-domain-v1"
REFERENCE_MATRIX_VERSION = "radi144-reference-v1"


@dataclass(frozen=True)
class Radi144CpuSafeExecutionInput:
    """Tenant-scoped, consent-checked input bundle for CPU-safe execution."""

    module_run_id: UUID
    tenant_id: UUID
    client_id: UUID
    session_id: UUID
    workflow_run_id: UUID
    goal_title: str
    goal_description: str = ""
    client_display_name: str = ""
    client_code: str | None = None
    consent_purpose: str = "analysis"
    manifest_version: str = "1.0.0"


class Radi144CpuSafeExecutionService:
    """Build validated Radi144Result DTOs with deterministic in-process logic."""

    def __init__(self, domain_service: Radi144DomainService | None = None) -> None:
        self.domain_service = domain_service or Radi144DomainService()

    def execute(self, execution_input: Radi144CpuSafeExecutionInput) -> Radi144Result:
        """Run deterministic CPU-safe Radi144 logic and return an unpersisted result."""
        context = Radi144InputContext(
            tenant_id=str(execution_input.tenant_id),
            client_id=str(execution_input.client_id),
            session_id=str(execution_input.session_id),
            goal_title=execution_input.goal_title,
            goal_description=execution_input.goal_description,
            client_display_name=execution_input.client_display_name,
            client_code=execution_input.client_code,
            consent_purpose=execution_input.consent_purpose,
        )
        plan = self.domain_service.build_plan(context)
        confidence = Radi144Confidence.model_validate(plan.confidence)
        synergy_seed = Radi144SynergySeed.model_validate(plan.synergy_seed)
        provenance = Radi144Provenance(
            algorithm_version=ALGORITHM_VERSION,
            manifest_version=execution_input.manifest_version,
            input_hash=self._input_hash(execution_input),
            reference_matrix_version=REFERENCE_MATRIX_VERSION,
            compute_backend="cpu",
            duration_ms=0,
        )
        return Radi144Result(
            module_run_id=execution_input.module_run_id,
            tenant_id=execution_input.tenant_id,
            client_id=execution_input.client_id,
            session_id=execution_input.session_id,
            workflow_run_id=execution_input.workflow_run_id,
            algorithm_version=ALGORITHM_VERSION,
            manifest_version=execution_input.manifest_version,
            compute_backend="cpu",
            coherence_scores=plan.coherence_scores,
            biofield_map=plan.biofield_map,
            confidence=confidence,
            synergy_seed=synergy_seed,
            provenance=provenance,
            retention=Radi144Retention(),
            client_projection=Radi144ClientProjectionPlaceholder(
                summary_label="Radi144 CPU-safe result pending role projection",
                quality_label="wellbeing quality pending",
            ),
        )

    def _input_hash(self, execution_input: Radi144CpuSafeExecutionInput) -> str:
        source = "|".join(
            [
                str(execution_input.tenant_id),
                str(execution_input.client_id),
                str(execution_input.session_id),
                str(execution_input.workflow_run_id),
                execution_input.goal_title,
                execution_input.goal_description,
                execution_input.client_display_name,
                execution_input.client_code or "",
                execution_input.consent_purpose,
                execution_input.manifest_version,
            ]
        )
        return sha256(source.encode("utf-8")).hexdigest()
