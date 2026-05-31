"""Tenant-scoped RadiBlohm engine routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.radiblohm import (
    RadiBlohmAdminProjection,
    RadiBlohmClientProjection,
    RadiBlohmJobCreateRequest,
    RadiBlohmJobStatusResponse,
    RadiBlohmResultPayload,
    RadiBlohmTherapistProjection,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.radiblohm.projection_builder import RadiBlohmProjectionBuilder
from app.services.radiblohm.result_writer import RadiBlohmResultWriter
from app.services.radiblohm.worker_runtime import (
    RadiBlohmJobRecordError,
    RadiBlohmJobRecordService,
    job_status,
)

router = APIRouter(prefix="/engines/radiblohm", tags=["radiblohm"])


@router.post(
    "/jobs",
    operation_id="createRadiBlohmJobRecord",
    response_model=RadiBlohmJobStatusResponse,
)
async def create_radiblohm_job_record(
    payload: RadiBlohmJobCreateRequest,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiBlohmJobStatusResponse:
    """Create a queued RadiBlohm ModuleRun job record."""
    try:
        module_run = await RadiBlohmJobRecordService(session).create_or_get_job_record(
            tenant_id=context.tenant_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            workflow_step_run_id=payload.workflow_step_run_id,
        )
        await session.commit()
    except RadiBlohmJobRecordError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.reason) from exc

    return RadiBlohmJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_created",
        message="RadiBlohm job record is queued for CPU-only worker execution.",
    )


@router.get(
    "/jobs/{job_id}",
    operation_id="getRadiBlohmJobStatus",
    response_model=RadiBlohmJobStatusResponse,
)
async def get_radiblohm_job_status(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiBlohmJobStatusResponse:
    """Return a tenant-scoped RadiBlohm job record."""
    module_run = await RadiBlohmJobRecordService(session).get_job_record(
        tenant_id=context.tenant_id,
        job_id=job_id,
    )
    if module_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiBlohm job not found",
        )
    return RadiBlohmJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_found",
        message="RadiBlohm job record found.",
    )


@router.get(
    "/jobs/{job_id}/result",
    operation_id="getRadiBlohmProjectedResult",
    response_model=(
        RadiBlohmClientProjection | RadiBlohmTherapistProjection | RadiBlohmAdminProjection
    ),
)
async def get_radiblohm_projected_result(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    role: Annotated[str, Query(pattern="^(client|therapist|admin)$")] = "client",
) -> RadiBlohmClientProjection | RadiBlohmTherapistProjection | RadiBlohmAdminProjection:
    """Return only role-safe projections, never raw result payloads."""
    stored = await RadiBlohmResultWriter(session).get_result(
        tenant_id=context.tenant_id,
        module_run_id=job_id,
    )
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiBlohm result not found",
        )
    payload = RadiBlohmResultPayload.model_validate(stored.result_payload_json)
    return RadiBlohmProjectionBuilder().build_projection(
        payload=payload,
        role=role,  # type: ignore[arg-type]
    )
