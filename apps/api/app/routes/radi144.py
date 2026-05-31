"""Tenant-scoped Radi144 Engine API runtime routes.

Runtime Route Gate scope: expose authenticated, tenant-guarded API endpoints.
Worker Job Gate scope: create/read ModuleRun job records only. These routes do
not start workers, persist results, or execute Radi144.
"""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.engine import ModuleProjection
from app.schemas.radi144_api import (
    Radi144JobCreateRequest,
    Radi144JobRecordStatus,
    Radi144RuntimeRouteStatusResponse,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.radi144.job_records import Radi144JobRecordError, Radi144JobRecordService
from app.services.radi144.projection_builder import (
    Radi144ClientProjection,
    Radi144TherapistProjection,
)

router = APIRouter(prefix="/engines/radi144", tags=["radi144"])


@router.post(
    "/jobs",
    operation_id="createRadi144JobRecord",
    response_model=Radi144RuntimeRouteStatusResponse,
)
async def create_radi144_job_record(
    payload: Radi144JobCreateRequest,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Radi144RuntimeRouteStatusResponse:
    """Create a queued ModuleRun job record without starting a worker."""
    try:
        module_run = await Radi144JobRecordService(session).create_or_get_job_record(
            tenant_id=context.tenant_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            workflow_step_run_id=payload.workflow_step_run_id,
        )
        await session.commit()
    except Radi144JobRecordError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.reason) from exc
    return Radi144RuntimeRouteStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        route_status="job_record_created_no_worker_runtime",
        job_status=cast(Radi144JobRecordStatus, module_run.status),
        message="Radi144 job record is queued; worker runtime and engine execution remain blocked.",
    )


@router.get(
    "/jobs/{job_id}",
    operation_id="getRadi144JobBoundaryStatus",
    response_model=Radi144RuntimeRouteStatusResponse,
)
async def get_radi144_job_boundary_status(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Radi144RuntimeRouteStatusResponse:
    """Return tenant-scoped Radi144 job record status without worker execution."""
    module_run = await Radi144JobRecordService(session).get_job_record(tenant_id=context.tenant_id, job_id=job_id)
    if module_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Radi144 job record not found")
    return Radi144RuntimeRouteStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        route_status="job_record_found_no_worker_runtime",
        job_status=cast(Radi144JobRecordStatus, module_run.status),
        message="Radi144 job record found; worker runtime and engine execution remain blocked.",
    )


@router.get(
    "/jobs/{job_id}/result",
    operation_id="getRadi144ProjectedResult",
    response_model=Radi144ClientProjection | Radi144TherapistProjection,
)
async def get_radi144_projected_result(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    role: Annotated[str, Query(pattern="^(client|therapist)$")] = "client",
) -> Radi144ClientProjection | Radi144TherapistProjection:
    """Read a stored Radi144 result only through the role-safe projection builder."""
    projection = await session.scalar(
        select(ModuleProjection).where(
            ModuleProjection.module_run_id == job_id,
            ModuleProjection.tenant_id == context.tenant_id,
            ModuleProjection.role == role,
        )
    )
    if projection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Radi144 result not found")
    if role == "client":
        return Radi144ClientProjection.model_validate(projection.projection_json)
    return Radi144TherapistProjection.model_validate(projection.projection_json)
