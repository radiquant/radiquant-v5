"""Tenant-scoped harmonization plan routes."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.audit import AuditLog
from app.models.harmonization import HarmonizationPlan
from app.models.session import ClientSession
from app.schemas.harmonization import (
    HarmonizationJobResponse,
    HarmonizationPlanCreate,
    HarmonizationPlanListResponse,
    HarmonizationPlanResponse,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.harmonization_worker import HarmonizationWorkerService
from app.services.hrv_gate import HRVGateService

harmonization_router = APIRouter(prefix="/sessions", tags=["harmonization"])


def _correlation_id(request: Request) -> str:
    header_value = request.headers.get("X-Correlation-ID")
    return header_value if header_value else str(uuid4())


async def _get_session_or_404(
    session: AsyncSession,
    tenant_id: UUID,
    session_id: UUID,
) -> ClientSession:
    client_session = await session.scalar(
        select(ClientSession).where(
            ClientSession.id == session_id,
            ClientSession.tenant_id == tenant_id,
        )
    )
    if client_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return client_session


async def _get_plan_or_404(
    session: AsyncSession,
    tenant_id: UUID,
    session_id: UUID,
    plan_id: UUID,
) -> HarmonizationPlan:
    plan = await session.scalar(
        select(HarmonizationPlan).where(
            HarmonizationPlan.id == plan_id,
            HarmonizationPlan.tenant_id == tenant_id,
            HarmonizationPlan.session_id == session_id,
        )
    )
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Harmonization plan not found",
        )
    return plan


@harmonization_router.post(
    "/{session_id}/harmonization/plans",
    operation_id="createHarmonizationPlan",
    response_model=HarmonizationPlanResponse,
    status_code=201,
)
async def create_harmonization_plan(
    session_id: UUID,
    payload: HarmonizationPlanCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> HarmonizationPlan:
    """Create a draft harmonization plan without approval side effects."""
    if payload.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Session mismatch",
        )
    await _get_session_or_404(session, context.tenant_id, session_id)
    plan = HarmonizationPlan(
        session_id=session_id,
        tenant_id=context.tenant_id,
        status="draft",
        plan_payload_json=payload.plan_payload_json,
        created_by_user_id=context.principal.user_id,
    )
    session.add(plan)
    await session.commit()
    return await _get_plan_or_404(session, context.tenant_id, session_id, plan.id)


@harmonization_router.post(
    "/{session_id}/harmonization/plans/{plan_id}/approve",
    operation_id="approveHarmonizationPlan",
    response_model=HarmonizationPlanResponse,
)
async def approve_harmonization_plan(
    session_id: UUID,
    plan_id: UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> HarmonizationPlan:
    """Approve a draft harmonization plan only through this explicit call."""
    await _get_session_or_404(session, context.tenant_id, session_id)
    plan = await _get_plan_or_404(session, context.tenant_id, session_id, plan_id)
    if plan.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Harmonization plan already approved",
        )
    plan.status = "approved"
    plan.approved_by_user_id = context.principal.user_id
    plan.approved_at = datetime.now(UTC)
    await session.flush()
    await session.execute(
        insert(AuditLog).values(
            tenant_id=context.tenant_id,
            actor_user_id=context.principal.user_id,
            action="harmonization_plan_approved",
            resource_type="harmonization_plan",
            resource_id=str(plan.id),
            reason="harmonization_plan_approved",
            metadata_json={"session_id": str(session_id)},
            correlation_id=_correlation_id(request),
        )
    )
    await session.commit()
    return await _get_plan_or_404(session, context.tenant_id, session_id, plan_id)


@harmonization_router.get(
    "/{session_id}/harmonization/plans",
    operation_id="listHarmonizationPlans",
    response_model=HarmonizationPlanListResponse,
)
async def list_harmonization_plans(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> HarmonizationPlanListResponse:
    """List tenant-scoped harmonization plans for a session."""
    await _get_session_or_404(session, context.tenant_id, session_id)
    plans = list(
        (
            await session.execute(
                select(HarmonizationPlan)
                .where(
                    HarmonizationPlan.tenant_id == context.tenant_id,
                    HarmonizationPlan.session_id == session_id,
                )
                .order_by(HarmonizationPlan.created_at.desc(), HarmonizationPlan.id)
            )
        )
        .scalars()
        .all()
    )
    return HarmonizationPlanListResponse(
        items=[HarmonizationPlanResponse.model_validate(plan) for plan in plans]
    )


@harmonization_router.post(
    "/harmonization/jobs",
    operation_id="startHarmonizationJob",
    response_model=HarmonizationJobResponse,
    status_code=201,
)
async def start_harmonization_job(
    plan_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    therapist_override: bool = False,
) -> HarmonizationJobResponse:
    plan = await session.scalar(
        select(HarmonizationPlan).where(
            HarmonizationPlan.id == plan_id,
            HarmonizationPlan.tenant_id == context.tenant_id,
        )
    )
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Harmonization plan not found",
        )
    gate_result = await HRVGateService().evaluate(
        session_id=plan.session_id,
        tenant_id=context.tenant_id,
        therapist_override=therapist_override,
        db=session,
    )
    if not gate_result.passed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="HRV coherence below threshold",
        )
    return await HarmonizationWorkerService().start(plan_id, context.tenant_id, session)


@harmonization_router.patch(
    "/harmonization/jobs/{job_id}/pause",
    operation_id="pauseHarmonizationJob",
    response_model=HarmonizationJobResponse,
)
async def pause_harmonization_job(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> HarmonizationJobResponse:
    return await HarmonizationWorkerService().pause(job_id, context.tenant_id, session)


@harmonization_router.patch(
    "/harmonization/jobs/{job_id}/resume",
    operation_id="resumeHarmonizationJob",
    response_model=HarmonizationJobResponse,
)
async def resume_harmonization_job(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> HarmonizationJobResponse:
    return await HarmonizationWorkerService().resume(job_id, context.tenant_id, session)


@harmonization_router.patch(
    "/harmonization/jobs/{job_id}/stop",
    operation_id="stopHarmonizationJob",
    response_model=HarmonizationJobResponse,
)
async def stop_harmonization_job(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> HarmonizationJobResponse:
    return await HarmonizationWorkerService().stop(job_id, context.tenant_id, session)
