"""Radi144 worker runtime service.

Worker CPU Execution Wiring Gate scope: process queued ModuleRun records through
the CPU-safe execution service and persist validated results via the existing
result writer transaction boundary. External queues, API-triggered execution,
projection writes, and GPU/CUDA paths remain blocked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import ClientProfile
from app.models.engine import ModuleRun
from app.models.session import ClientSession, SessionGoal
from app.models.workflow import WorkflowRun
from app.schemas.event import EventEnvelopeCreate
from app.services.consent import ConsentRequiredError, ConsentService
from app.services.event_registry import EventWriter
from app.services.radi144.cpu_safe_execution import Radi144CpuSafeExecutionInput, Radi144CpuSafeExecutionService
from app.services.radi144.result_writer import Radi144ResultWriteError, Radi144ResultWriter

Radi144WorkerRuntimeStatus = Literal[
    "no_queued_job",
    "result_stored_cpu_safe",
    "failed_closed_consent_required",
    "failed_closed_result_write_rejected",
    "failed_closed_invalid_job_context",
]
Radi144WorkerRuntimeReason = Literal[
    "no_queued_radi144_job",
    "cpu_safe_result_stored",
    "consent_required",
    "result_write_rejected",
    "invalid_job_context",
]


@dataclass(frozen=True)
class Radi144WorkerRuntimeOutcome:
    """Public-safe worker runtime outcome without raw/debug/internal payloads."""

    status: Radi144WorkerRuntimeStatus
    module_run_id: UUID | None
    tenant_id: UUID | None
    reason: Radi144WorkerRuntimeReason
    cpu_execution_enabled: bool = True
    gpu_cuda_execution_enabled: bool = False
    result_written: bool = False


class Radi144WorkerRuntimeService:
    """Radi144 worker runtime for CPU-safe execution only."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        cpu_execution_service: Radi144CpuSafeExecutionService | None = None,
        event_writer: EventWriter | None = None,
    ) -> None:
        self.session = session
        self.cpu_execution_service = cpu_execution_service or Radi144CpuSafeExecutionService()
        self.event_writer = event_writer or EventWriter(session)

    async def process_next_queued(self, *, tenant_id: UUID | None = None) -> Radi144WorkerRuntimeOutcome:
        """Process the next queued Radi144 job using CPU-safe execution.

        The caller owns transaction commit/rollback. This method flushes state
        through the result writer but must not commit, build projections, call
        GPU/CUDA paths, or use external queues.
        """
        statement = (
            select(ModuleRun, WorkflowRun, ClientSession, SessionGoal, ClientProfile)
            .join(WorkflowRun, WorkflowRun.id == ModuleRun.workflow_run_id)
            .join(ClientSession, ClientSession.id == ModuleRun.session_id)
            .join(SessionGoal, SessionGoal.id == ClientSession.goal_id)
            .join(ClientProfile, ClientProfile.id == ClientSession.client_id)
            .where(
                ModuleRun.module_id == "radi144",
                ModuleRun.status == "queued",
                ModuleRun.tenant_id == WorkflowRun.tenant_id,
                ModuleRun.tenant_id == ClientSession.tenant_id,
                ModuleRun.tenant_id == SessionGoal.tenant_id,
                ModuleRun.tenant_id == ClientProfile.tenant_id,
                WorkflowRun.session_id == ClientSession.id,
                SessionGoal.client_id == ClientSession.client_id,
            )
            .order_by(ModuleRun.created_at)
        )
        if tenant_id is not None:
            statement = statement.where(ModuleRun.tenant_id == tenant_id)
        row = (await self.session.execute(statement)).first()
        if row is None:
            return Radi144WorkerRuntimeOutcome(
                status="no_queued_job",
                module_run_id=None,
                tenant_id=tenant_id,
                reason="no_queued_radi144_job",
                cpu_execution_enabled=True,
                result_written=False,
            )
        module_run, _workflow_run, client_session, goal, client = row._tuple()
        await self._append_worker_event(module_run=module_run, event_type="job.running", reason="cpu_safe_worker_started")
        await self._append_worker_event(module_run=module_run, event_type="module.radi144.started", reason="cpu_safe_execution_started")

        try:
            await ConsentService(self.session).assert_analysis_allowed(tenant_id=module_run.tenant_id, client_id=client_session.client_id)
        except ConsentRequiredError:
            module_run.status = "failed_closed"
            await self._append_worker_event(module_run=module_run, event_type="module.radi144.failed", reason="consent_required")
            await self._append_worker_event(module_run=module_run, event_type="job.failed", reason="consent_required")
            await self.session.flush()
            return Radi144WorkerRuntimeOutcome(
                status="failed_closed_consent_required",
                module_run_id=module_run.id,
                tenant_id=module_run.tenant_id,
                reason="consent_required",
                result_written=False,
            )

        execution_input = Radi144CpuSafeExecutionInput(
            module_run_id=module_run.id,
            tenant_id=module_run.tenant_id,
            client_id=client_session.client_id,
            session_id=module_run.session_id,
            workflow_run_id=module_run.workflow_run_id,
            goal_title=goal.title,
            goal_description=goal.description,
            client_display_name=client.display_name,
            client_code=client.client_code,
            consent_purpose="analysis",
        )
        result = self.cpu_execution_service.execute(execution_input)
        try:
            await Radi144ResultWriter(self.session).persist_result(result=result, workflow_step_run_id=module_run.workflow_step_run_id)
        except Radi144ResultWriteError:
            module_run.status = "failed_closed"
            await self._append_worker_event(module_run=module_run, event_type="module.radi144.failed", reason="result_write_rejected")
            await self._append_worker_event(module_run=module_run, event_type="job.failed", reason="result_write_rejected")
            await self.session.flush()
            return Radi144WorkerRuntimeOutcome(
                status="failed_closed_result_write_rejected",
                module_run_id=module_run.id,
                tenant_id=module_run.tenant_id,
                reason="result_write_rejected",
                result_written=False,
            )

        await self._append_worker_event(module_run=module_run, event_type="module.radi144.completed", reason="cpu_safe_result_stored")
        await self._append_worker_event(module_run=module_run, event_type="job.done", reason="cpu_safe_result_stored")
        return Radi144WorkerRuntimeOutcome(
            status="result_stored_cpu_safe",
            module_run_id=module_run.id,
            tenant_id=module_run.tenant_id,
            reason="cpu_safe_result_stored",
            result_written=True,
        )

    async def _append_worker_event(self, *, module_run: ModuleRun, event_type: str, reason: str) -> None:
        """Append public-safe event-truth records for worker progress."""
        await self.event_writer.append(
            EventEnvelopeCreate(
                event_type=event_type,
                occurred_at=datetime.now(UTC),
                tenant_id=module_run.tenant_id,
                correlation_id=f"radi144:{module_run.id}",
                session_id=module_run.session_id,
                workflow_run_id=module_run.workflow_run_id,
                workflow_step_run_id=module_run.workflow_step_run_id,
                resource_type="module_run",
                resource_id=str(module_run.id),
                payload={
                    "module_id": "radi144",
                    "module_run_id": str(module_run.id),
                    "status": module_run.status,
                    "reason": reason,
                    "compute_backend": "cpu",
                    "gpu_cuda_execution_enabled": False,
                },
            )
        )
