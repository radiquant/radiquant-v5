"""Tenant-scoped RadiThoms engine routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.radithoms import (
    RadiThomsAdminProjection,
    RadiThomsClientProjection,
    RadiThomsJobCreateRequest,
    RadiThomsJobStatusResponse,
    RadiThomsResultPayload,
    RadiThomsTherapistProjection,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.radithoms.projection_builder import RadiThomsProjectionBuilder
from app.services.radithoms.result_writer import RadiThomsResultWriter
from app.services.radithoms.worker_runtime import (
    RadiThomsJobRecordError,
    RadiThomsJobRecordService,
    job_status,
)

router = APIRouter(prefix="/engines/radithoms", tags=["radithoms"])


@router.post(
    "/jobs",
    operation_id="createRadiThomsJobRecord",
    response_model=RadiThomsJobStatusResponse,
)
async def create_radithoms_job_record(
    payload: RadiThomsJobCreateRequest,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiThomsJobStatusResponse:
    """Create a queued RadiThoms ModuleRun job record."""
    try:
        module_run = await RadiThomsJobRecordService(session).create_or_get_job_record(
            tenant_id=context.tenant_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            workflow_step_run_id=payload.workflow_step_run_id,
        )
        await session.commit()
    except RadiThomsJobRecordError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.reason) from exc

    return RadiThomsJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_created",
        message="RadiThoms job record is queued for CPU-only worker execution.",
    )


@router.get(
    "/jobs/{job_id}",
    operation_id="getRadiThomsJobStatus",
    response_model=RadiThomsJobStatusResponse,
)
async def get_radithoms_job_status(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiThomsJobStatusResponse:
    """Return a tenant-scoped RadiThoms job record."""
    module_run = await RadiThomsJobRecordService(session).get_job_record(
        tenant_id=context.tenant_id,
        job_id=job_id,
    )
    if module_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiThoms job not found",
        )
    return RadiThomsJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_found",
        message="RadiThoms job record found.",
    )


@router.get(
    "/jobs/{job_id}/result",
    operation_id="getRadiThomsProjectedResult",
    response_model=(
        RadiThomsClientProjection | RadiThomsTherapistProjection | RadiThomsAdminProjection
    ),
)
async def get_radithoms_projected_result(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    role: Annotated[str, Query(pattern="^(client|therapist|admin)$")] = "client",
) -> RadiThomsClientProjection | RadiThomsTherapistProjection | RadiThomsAdminProjection:
    """Return only role-safe projections, never raw result payloads."""
    stored = await RadiThomsResultWriter(session).get_result(
        tenant_id=context.tenant_id,
        module_run_id=job_id,
    )
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiThoms result not found",
        )
    payload = RadiThomsResultPayload.model_validate(stored.result_payload_json)
    return RadiThomsProjectionBuilder().build_projection(
        payload=payload,
        role=role,  # type: ignore[arg-type]
    )
