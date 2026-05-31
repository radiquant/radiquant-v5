"""RadiThoms worker runtime and job-record services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import ClientProfile
from app.models.engine import ModuleRun
from app.models.session import ClientSession, SessionGoal
from app.models.workflow import WorkflowRun, WorkflowStepRun
from app.schemas.radithoms import RadiThomsJobStatus
from app.services.radithoms.engine import RadiThomsEngine, RadiThomsExecutionInput
from app.services.radithoms.result_writer import (
    RadiThomsResultWriteError,
    RadiThomsResultWriter,
)

RadiThomsWorkerStatus = Literal[
    "no_queued_job",
    "result_stored_cpu_safe",
    "failed_closed_result_write_rejected",
    "failed_closed_invalid_job_context",
]


class RadiThomsJobRecordError(ValueError):
    """Raised when a RadiThoms job record cannot be created safely."""

    public_detail = "RadiThoms job record rejected"

    def __init__(self, reason: str) -> None:
        super().__init__(self.public_detail)
        self.reason = reason


@dataclass(frozen=True)
class RadiThomsWorkerOutcome:
    """Public-safe RadiThoms worker runtime outcome."""

    status: RadiThomsWorkerStatus
    module_run_id: UUID | None
    tenant_id: UUID | None
    reason: str
    result_written: bool = False
    cpu_execution_enabled: bool = True
    hardware_entropy_enabled: bool = False


class RadiThomsJobRecordService:
    """Create/read RadiThoms ModuleRun job records without executing work."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_or_get_job_record(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        workflow_run_id: UUID,
        workflow_step_run_id: UUID,
    ) -> ModuleRun:
        """Create a queued job record or return the existing record."""
        workflow_step = await self.session.scalar(
            select(WorkflowStepRun)
            .join(WorkflowRun, WorkflowRun.id == WorkflowStepRun.workflow_run_id)
            .where(
                WorkflowStepRun.id == workflow_step_run_id,
                WorkflowStepRun.tenant_id == tenant_id,
                WorkflowStepRun.workflow_run_id == workflow_run_id,
                WorkflowStepRun.module_id == "radithoms",
                WorkflowRun.id == workflow_run_id,
                WorkflowRun.tenant_id == tenant_id,
                WorkflowRun.session_id == session_id,
            )
        )
        if workflow_step is None:
            raise RadiThomsJobRecordError("workflow_step_not_found_for_tenant")

        existing = await self.session.scalar(
            select(ModuleRun).where(
                ModuleRun.tenant_id == tenant_id,
                ModuleRun.workflow_step_run_id == workflow_step_run_id,
                ModuleRun.module_id == "radithoms",
            )
        )
        if existing is not None:
            return existing

        module_run = ModuleRun(
            tenant_id=tenant_id,
            session_id=session_id,
            workflow_run_id=workflow_run_id,
            workflow_step_run_id=workflow_step_run_id,
            module_id="radithoms",
            phase="analyze",
            status="queued",
            schema_id="radithoms_result_v1",
            job_contract_schema_id="radithoms_engine_job_v1",
        )
        self.session.add(module_run)
        await self.session.flush()
        return module_run

    async def get_job_record(self, *, tenant_id: UUID, job_id: UUID) -> ModuleRun | None:
        """Return a tenant-scoped RadiThoms job record by ModuleRun id."""
        return await self.session.scalar(
            select(ModuleRun).where(
                ModuleRun.id == job_id,
                ModuleRun.tenant_id == tenant_id,
                ModuleRun.module_id == "radithoms",
            )
        )


class RadiThomsWorkerRuntimeService:
    """Process queued RadiThoms jobs using CPU-only execution."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        engine: RadiThomsEngine | None = None,
    ) -> None:
        self.session = session
        self.engine = engine or RadiThomsEngine()

    async def process_next_queued(
        self,
        *,
        tenant_id: UUID | None = None,
    ) -> RadiThomsWorkerOutcome:
        """Process the next queued RadiThoms job without committing."""
        statement = (
            select(ModuleRun, WorkflowRun, ClientSession, SessionGoal, ClientProfile)
            .join(WorkflowRun, WorkflowRun.id == ModuleRun.workflow_run_id)
            .join(ClientSession, ClientSession.id == ModuleRun.session_id)
            .join(SessionGoal, SessionGoal.id == ClientSession.goal_id)
            .join(ClientProfile, ClientProfile.id == ClientSession.client_id)
            .where(
                ModuleRun.module_id == "radithoms",
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
            return RadiThomsWorkerOutcome(
                status="no_queued_job",
                module_run_id=None,
                tenant_id=tenant_id,
                reason="no_queued_radithoms_job",
            )

        module_run, _workflow_run, client_session, goal, client = row._tuple()
        result = self.engine.execute(
            RadiThomsExecutionInput(
                module_run_id=module_run.id,
                tenant_id=module_run.tenant_id,
                client_id=client_session.client_id,
                session_id=module_run.session_id,
                workflow_run_id=module_run.workflow_run_id,
                goal_title=goal.title,
                goal_description=goal.description,
                client_display_name=client.display_name,
                client_code=client.client_code,
            )
        )
        try:
            await RadiThomsResultWriter(self.session).persist_result(result=result)
        except RadiThomsResultWriteError:
            module_run.status = "failed_closed"
            await self.session.flush()
            return RadiThomsWorkerOutcome(
                status="failed_closed_result_write_rejected",
                module_run_id=module_run.id,
                tenant_id=module_run.tenant_id,
                reason="result_write_rejected",
                result_written=False,
            )

        return RadiThomsWorkerOutcome(
            status="result_stored_cpu_safe",
            module_run_id=module_run.id,
            tenant_id=module_run.tenant_id,
            reason="cpu_safe_result_stored",
            result_written=True,
        )


def job_status(module_run: ModuleRun) -> RadiThomsJobStatus:
    """Cast a ModuleRun status into the public RadiThoms job status type."""
    return module_run.status  # type: ignore[return-value]
