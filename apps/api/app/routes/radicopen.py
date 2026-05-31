"""Tenant-scoped RadiCopen engine routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.radicopen import (
    RadiCopenAdminProjection,
    RadiCopenClientProjection,
    RadiCopenJobCreateRequest,
    RadiCopenJobStatusResponse,
    RadiCopenResultPayload,
    RadiCopenTherapistProjection,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.radicopen.projection_builder import RadiCopenProjectionBuilder
from app.services.radicopen.result_writer import RadiCopenResultWriter
from app.services.radicopen.worker_runtime import (
    RadiCopenJobRecordError,
    RadiCopenJobRecordService,
    job_status,
)

router = APIRouter(prefix="/engines/radicopen", tags=["radicopen"])


@router.post(
    "/jobs",
    operation_id="createRadiCopenJobRecord",
    response_model=RadiCopenJobStatusResponse,
)
async def create_radicopen_job_record(
    payload: RadiCopenJobCreateRequest,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiCopenJobStatusResponse:
    """Create a queued RadiCopen ModuleRun job record."""
    try:
        module_run = await RadiCopenJobRecordService(session).create_or_get_job_record(
            tenant_id=context.tenant_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            workflow_step_run_id=payload.workflow_step_run_id,
        )
        await session.commit()
    except RadiCopenJobRecordError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.reason) from exc

    return RadiCopenJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_created",
        message="RadiCopen job record is queued for CPU-only worker execution.",
    )


@router.get(
    "/jobs/{job_id}",
    operation_id="getRadiCopenJobStatus",
    response_model=RadiCopenJobStatusResponse,
)
async def get_radicopen_job_status(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiCopenJobStatusResponse:
    """Return a tenant-scoped RadiCopen job record."""
    module_run = await RadiCopenJobRecordService(session).get_job_record(
        tenant_id=context.tenant_id,
        job_id=job_id,
    )
    if module_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiCopen job not found",
        )
    return RadiCopenJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_found",
        message="RadiCopen job record found.",
    )


@router.get(
    "/jobs/{job_id}/result",
    operation_id="getRadiCopenProjectedResult",
    response_model=(
        RadiCopenClientProjection | RadiCopenTherapistProjection | RadiCopenAdminProjection
    ),
)
async def get_radicopen_projected_result(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    role: Annotated[str, Query(pattern="^(client|therapist|admin)$")] = "client",
) -> RadiCopenClientProjection | RadiCopenTherapistProjection | RadiCopenAdminProjection:
    """Return only role-safe projections, never raw result payloads."""
    stored = await RadiCopenResultWriter(session).get_result(
        tenant_id=context.tenant_id,
        module_run_id=job_id,
    )
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiCopen result not found",
        )
    payload = RadiCopenResultPayload.model_validate(stored.result_payload_json)
    return RadiCopenProjectionBuilder().build_projection(
        payload=payload,
        role=role,  # type: ignore[arg-type]
    )
