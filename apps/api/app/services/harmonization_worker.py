"""Harmonization job lifecycle service."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.harmonization import HarmonizationJob, HarmonizationPlan


class HarmonizationWorkerService:
    """Start, pause, resume, and stop tenant-scoped harmonization jobs."""

    async def _wait_for_hardware_ack(self, job: HarmonizationJob) -> bool:
        await asyncio.sleep(0)
        return False

    async def start(
        self,
        plan_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> HarmonizationJob:
        plan = await db.scalar(
            select(HarmonizationPlan).where(
                HarmonizationPlan.id == plan_id,
                HarmonizationPlan.tenant_id == tenant_id,
            )
        )
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Harmonization plan not found",
            )
        if plan.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Harmonization plan must be approved before job start",
            )

        job = HarmonizationJob(plan_id=plan.id, tenant_id=tenant_id, status="queued")
        db.add(job)
        await db.flush()

        hardware_fallback = False
        try:
            hardware_ack = await asyncio.wait_for(self._wait_for_hardware_ack(job), timeout=5)
        except TimeoutError:
            hardware_ack = False
            hardware_fallback = True

        job.hardware_ack = hardware_ack
        job.status = "running"
        job.started_at = datetime.now(UTC)
        await db.flush()
        await self._append_audit_event(
            db=db,
            tenant_id=tenant_id,
            action="harmonization_job_started",
            job=job,
            metadata_json={
                "plan_id": str(plan.id),
                "hardware_ack": hardware_ack,
                "hardware_fallback": hardware_fallback or not hardware_ack,
            },
        )
        await db.commit()
        return job

    async def pause(
        self,
        job_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> HarmonizationJob:
        job = await self._get_job_or_404(db, tenant_id, job_id)
        if job.status != "running":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Harmonization job is not running",
            )
        job.status = "paused"
        job.paused_at = datetime.now(UTC)
        await db.commit()
        return job

    async def resume(
        self,
        job_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> HarmonizationJob:
        job = await self._get_job_or_404(db, tenant_id, job_id)
        if job.status != "paused":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Harmonization job is not paused",
            )
        job.status = "running"
        await db.commit()
        return job

    async def stop(
        self,
        job_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> HarmonizationJob:
        job = await self._get_job_or_404(db, tenant_id, job_id)
        job.status = "cancelled"
        job.completed_at = datetime.now(UTC)
        await db.flush()
        await self._append_audit_event(
            db=db,
            tenant_id=tenant_id,
            action="harmonization_job_cancelled",
            job=job,
            metadata_json={"plan_id": str(job.plan_id)},
        )
        await db.commit()
        return job

    async def _get_job_or_404(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
    ) -> HarmonizationJob:
        job = await db.scalar(
            select(HarmonizationJob).where(
                HarmonizationJob.id == job_id,
                HarmonizationJob.tenant_id == tenant_id,
            )
        )
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Harmonization job not found",
            )
        return job

    async def _append_audit_event(
        self,
        *,
        db: AsyncSession,
        tenant_id: UUID,
        action: str,
        job: HarmonizationJob,
        metadata_json: dict[str, object],
    ) -> None:
        await db.execute(
            insert(AuditLog).values(
                tenant_id=tenant_id,
                actor_user_id=None,
                action=action,
                resource_type="harmonization_job",
                resource_id=str(job.id),
                reason=action,
                metadata_json=metadata_json,
                correlation_id=str(uuid4()),
            )
        )
