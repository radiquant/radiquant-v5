"""Tenant-scoped RadiWorks engine routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.radiworks import (
    RadiWorksAdminProjection,
    RadiWorksClientProjection,
    RadiWorksJobCreateRequest,
    RadiWorksJobStatusResponse,
    RadiWorksResultPayload,
    RadiWorksTherapistProjection,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.radiworks.projection_builder import RadiWorksProjectionBuilder
from app.services.radiworks.result_writer import RadiWorksResultWriter
from app.services.radiworks.worker_runtime import (
    RadiWorksJobRecordError,
    RadiWorksJobRecordService,
    job_status,
)

router = APIRouter(prefix="/engines/radiworks", tags=["radiworks"])


@router.post(
    "/jobs",
    operation_id="createRadiWorksJobRecord",
    response_model=RadiWorksJobStatusResponse,
)
async def create_radiworks_job_record(
    payload: RadiWorksJobCreateRequest,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiWorksJobStatusResponse:
    """Create a queued RadiWorks ModuleRun job record."""
    try:
        module_run = await RadiWorksJobRecordService(session).create_or_get_job_record(
            tenant_id=context.tenant_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            workflow_step_run_id=payload.workflow_step_run_id,
        )
        await session.commit()
    except RadiWorksJobRecordError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.reason) from exc

    return RadiWorksJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_created",
        message="RadiWorks job record is queued for CPU-only worker execution.",
    )


@router.get(
    "/jobs/{job_id}",
    operation_id="getRadiWorksJobStatus",
    response_model=RadiWorksJobStatusResponse,
)
async def get_radiworks_job_status(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiWorksJobStatusResponse:
    """Return a tenant-scoped RadiWorks job record."""
    module_run = await RadiWorksJobRecordService(session).get_job_record(
        tenant_id=context.tenant_id,
        job_id=job_id,
    )
    if module_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RadiWorks job not found")
    return RadiWorksJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_found",
        message="RadiWorks job record found.",
    )


@router.get(
    "/jobs/{job_id}/result",
    operation_id="getRadiWorksProjectedResult",
    response_model=(
        RadiWorksClientProjection | RadiWorksTherapistProjection | RadiWorksAdminProjection
    ),
)
async def get_radiworks_projected_result(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    role: Annotated[str, Query(pattern="^(client|therapist|admin)$")] = "client",
) -> RadiWorksClientProjection | RadiWorksTherapistProjection | RadiWorksAdminProjection:
    """Return only role-safe projections, never raw result payloads."""
    stored = await RadiWorksResultWriter(session).get_result(
        tenant_id=context.tenant_id,
        module_run_id=job_id,
    )
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiWorks result not found",
        )
    payload = RadiWorksResultPayload.model_validate(stored.result_payload_json)
    return RadiWorksProjectionBuilder().build_projection(
        payload=payload,
        role=role,  # type: ignore[arg-type]
    )
