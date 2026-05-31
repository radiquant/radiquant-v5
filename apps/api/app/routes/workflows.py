"""Tenant-scoped Workflow API Gate routes.

Scope: create and list manifest-derived workflow plans. Workflow UI, realtime,
engine execution, module results, and progress streams remain blocked.
"""

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.audit import AuditAction
from app.models.session import ClientSession, SessionStatus
from app.models.workflow import (
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowStepRun,
    WorkflowStepRunStatus,
)
from app.schemas.workflow import (
    WorkflowRunCreateRequest,
    WorkflowRunListResponse,
    WorkflowRunResponse,
)
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.audit import AuditService
from app.services.consent import ConsentRequiredError, ConsentService
from app.services.workflow_manifest import (
    UnknownWorkflowError,
    WorkflowManifestService,
    WorkflowNotPlannableError,
)

router = APIRouter(tags=["workflows"])


def _correlation_id(request: Request) -> str:
    header_value = request.headers.get("X-Correlation-ID")
    return header_value if header_value else str(uuid4())


async def _get_session_or_404(session: AsyncSession, tenant_id: UUID, session_id: UUID) -> ClientSession:
    client_session = await session.scalar(select(ClientSession).where(ClientSession.id == session_id, ClientSession.tenant_id == tenant_id))
    if client_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return client_session


async def _get_workflow_run_or_404(session: AsyncSession, tenant_id: UUID, workflow_run_id: UUID) -> WorkflowRun:
    workflow_run = await session.scalar(
        select(WorkflowRun)
        .options(selectinload(WorkflowRun.steps))
        .where(WorkflowRun.id == workflow_run_id, WorkflowRun.tenant_id == tenant_id)
    )
    if workflow_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return workflow_run


def _consent_denied(exc: ConsentRequiredError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.public_detail)


@router.post(
    "/sessions/{session_id}/workflow-runs",
    operation_id="createWorkflowRun",
    response_model=WorkflowRunResponse,
    status_code=201,
)
async def create_workflow_run(
    session_id: UUID,
    payload: WorkflowRunCreateRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> WorkflowRun:
    """Create a manifest-derived workflow plan for an active tenant-owned session."""
    client_session = await _get_session_or_404(session, context.tenant_id, session_id)
    if client_session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is not active")

    try:
        plan = WorkflowManifestService().build_plan(payload.workflow_id)
    except UnknownWorkflowError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.public_detail) from exc
    except WorkflowNotPlannableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.public_detail) from exc

    consent_service = ConsentService(session)
    try:
        for purpose in plan.required_consent_purposes:
            await consent_service.assert_active_consent(
                tenant_id=context.tenant_id,
                client_id=client_session.client_id,
                purpose=purpose,
            )
    except ConsentRequiredError as exc:
        raise _consent_denied(exc) from exc

    workflow_run = WorkflowRun(
        tenant_id=context.tenant_id,
        session_id=session_id,
        workflow_id=plan.workflow_id,
        workflow_slug=plan.workflow_slug,
        status=WorkflowRunStatus.PLANNED,
        created_by_user_id=context.principal.user_id,
        updated_by_user_id=context.principal.user_id,
    )
    session.add(workflow_run)
    await session.flush()

    for step in plan.steps:
        session.add(
            WorkflowStepRun(
                tenant_id=context.tenant_id,
                workflow_run_id=workflow_run.id,
                step_index=step.step_index,
                module_id=step.module_id,
                phase=step.phase,
                status=WorkflowStepRunStatus.PLANNED,
            )
        )

    await session.flush()
    await AuditService(session).append(
        tenant_id=context.tenant_id,
        actor_user_id=context.principal.user_id,
        action=AuditAction.WORKFLOW_PLAN,
        resource_type="workflow_run",
        resource_id=str(workflow_run.id),
        reason="workflow_run_planned",
        correlation_id=_correlation_id(request),
        metadata_json={
            "session_id": str(session_id),
            "workflow_id": plan.workflow_id,
            "step_count": len(plan.steps),
            "required_consent_purposes": [purpose.value for purpose in plan.required_consent_purposes],
        },
    )
    await session.commit()
    return await _get_workflow_run_or_404(session, context.tenant_id, workflow_run.id)


@router.get(
    "/sessions/{session_id}/workflow-runs",
    operation_id="listSessionWorkflowRuns",
    response_model=WorkflowRunListResponse,
)
async def list_session_workflow_runs(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WorkflowRunListResponse:
    """List manifest-derived workflow runs for a tenant-owned session."""
    await _get_session_or_404(session, context.tenant_id, session_id)
    statement = (
        select(WorkflowRun)
        .options(selectinload(WorkflowRun.steps))
        .where(WorkflowRun.tenant_id == context.tenant_id, WorkflowRun.session_id == session_id)
        .order_by(WorkflowRun.created_at.desc(), WorkflowRun.id)
        .limit(limit)
        .offset(offset)
    )
    workflow_runs = list((await session.execute(statement)).scalars().all())
    return WorkflowRunListResponse(
        items=[WorkflowRunResponse.model_validate(workflow_run) for workflow_run in workflow_runs],
        limit=limit,
        offset=offset,
    )
