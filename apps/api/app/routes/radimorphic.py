"""Tenant-scoped RadiMorphic engine routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.radimorphic import (
    RadiMorphicAdminProjection,
    RadiMorphicClientProjection,
    RadiMorphicJobCreateRequest,
    RadiMorphicJobStatusResponse,
    RadiMorphicResultPayload,
    RadiMorphicTherapistProjection,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.radimorphic.projection_builder import RadiMorphicProjectionBuilder
from app.services.radimorphic.result_writer import RadiMorphicResultWriter
from app.services.radimorphic.worker_runtime import (
    RadiMorphicJobRecordError,
    RadiMorphicJobRecordService,
    job_status,
)

router = APIRouter(prefix="/engines/radimorphic", tags=["radimorphic"])


@router.post(
    "/jobs",
    operation_id="createRadiMorphicJobRecord",
    response_model=RadiMorphicJobStatusResponse,
)
async def create_radimorphic_job_record(
    payload: RadiMorphicJobCreateRequest,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiMorphicJobStatusResponse:
    """Create a queued RadiMorphic ModuleRun job record."""
    try:
        module_run = await RadiMorphicJobRecordService(session).create_or_get_job_record(
            tenant_id=context.tenant_id,
            session_id=payload.session_id,
            workflow_run_id=payload.workflow_run_id,
            workflow_step_run_id=payload.workflow_step_run_id,
        )
        await session.commit()
    except RadiMorphicJobRecordError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.reason) from exc

    return RadiMorphicJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_created",
        message="RadiMorphic job record is queued for CPU-only worker execution.",
    )


@router.get(
    "/jobs/{job_id}",
    operation_id="getRadiMorphicJobStatus",
    response_model=RadiMorphicJobStatusResponse,
)
async def get_radimorphic_job_status(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RadiMorphicJobStatusResponse:
    """Return a tenant-scoped RadiMorphic job record."""
    module_run = await RadiMorphicJobRecordService(session).get_job_record(
        tenant_id=context.tenant_id,
        job_id=job_id,
    )
    if module_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiMorphic job not found",
        )
    return RadiMorphicJobStatusResponse(
        tenant_id=context.tenant_id,
        job_id=module_run.id,
        session_id=module_run.session_id,
        workflow_run_id=module_run.workflow_run_id,
        workflow_step_run_id=module_run.workflow_step_run_id,
        job_status=job_status(module_run),
        route_status="job_record_found",
        message="RadiMorphic job record found.",
    )


@router.get(
    "/jobs/{job_id}/result",
    operation_id="getRadiMorphicProjectedResult",
    response_model=(
        RadiMorphicClientProjection | RadiMorphicTherapistProjection | RadiMorphicAdminProjection
    ),
)
async def get_radimorphic_projected_result(
    job_id: UUID,
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    role: Annotated[str, Query(pattern="^(client|therapist|admin)$")] = "client",
) -> RadiMorphicClientProjection | RadiMorphicTherapistProjection | RadiMorphicAdminProjection:
    """Return only role-safe projections, never raw result payloads."""
    stored = await RadiMorphicResultWriter(session).get_result(
        tenant_id=context.tenant_id,
        module_run_id=job_id,
    )
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RadiMorphic result not found",
        )
    payload = RadiMorphicResultPayload.model_validate(stored.result_payload_json)
    return RadiMorphicProjectionBuilder().build_projection(
        payload=payload,
        role=role,  # type: ignore[arg-type]
    )
