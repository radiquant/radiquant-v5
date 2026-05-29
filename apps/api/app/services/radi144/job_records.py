"""Radi144 API job record service.

Worker Job Gate Decision scope: create tenant-scoped ModuleRun job records
without starting workers, writing results, building projections, or executing
Radi144.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engine import ModuleRun
from app.models.workflow import WorkflowRun, WorkflowStepRun


class Radi144JobRecordError(ValueError):
    """Raised when a Radi144 job record cannot be created safely."""

    public_detail = "Radi144 job record rejected"

    def __init__(self, reason: str) -> None:
        super().__init__(self.public_detail)
        self.reason = reason


class Radi144JobRecordService:
    """Create/read Radi144 ModuleRun job records without worker execution."""

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
        """Create a queued job record or return the existing record.

        The caller owns transaction commit/rollback. This method flushes only so
        the generated ModuleRun id is available to the API response.
        """
        workflow_step = await self.session.scalar(
            select(WorkflowStepRun)
            .join(WorkflowRun, WorkflowRun.id == WorkflowStepRun.workflow_run_id)
            .where(
                WorkflowStepRun.id == workflow_step_run_id,
                WorkflowStepRun.tenant_id == tenant_id,
                WorkflowStepRun.workflow_run_id == workflow_run_id,
                WorkflowStepRun.module_id == "radi144",
                WorkflowStepRun.phase == "diagnose",
                WorkflowRun.id == workflow_run_id,
                WorkflowRun.tenant_id == tenant_id,
                WorkflowRun.session_id == session_id,
            )
        )
        if workflow_step is None:
            raise Radi144JobRecordError("workflow_step_not_found_for_tenant")

        existing = await self.session.scalar(
            select(ModuleRun).where(
                ModuleRun.tenant_id == tenant_id,
                ModuleRun.workflow_step_run_id == workflow_step_run_id,
                ModuleRun.module_id == "radi144",
            )
        )
        if existing is not None:
            return existing

        module_run = ModuleRun(
            tenant_id=tenant_id,
            session_id=session_id,
            workflow_run_id=workflow_run_id,
            workflow_step_run_id=workflow_step_run_id,
            module_id="radi144",
            phase="diagnose",
            status="queued",
            schema_id="radi144_result_v1",
            job_contract_schema_id="radi144_engine_job_v1",
        )
        self.session.add(module_run)
        await self.session.flush()
        return module_run

    async def get_job_record(self, *, tenant_id: UUID, job_id: UUID) -> ModuleRun | None:
        """Return a tenant-scoped Radi144 job record by ModuleRun id."""
        return await self.session.scalar(
            select(ModuleRun).where(ModuleRun.id == job_id, ModuleRun.tenant_id == tenant_id, ModuleRun.module_id == "radi144")
        )
