"""Tenant-scoped session routes.

This router starts and tracks minimal client sessions only. Workflow, realtime,
and engine execution are intentionally excluded until later contract gates.
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.audit import AuditAction
from app.models.client import ClientProfile
from app.models.session import ClientSession, SessionGoal, SessionStatus
from app.schemas.session import SessionCreateRequest, SessionListResponse, SessionResponse, SessionStatusUpdateRequest
from app.security.tenant_guard import TenantContext, require_tenant_context
from app.services.audit import AuditService
from app.services.consent import ConsentRequiredError, ConsentService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _correlation_id(request: Request) -> str:
    header_value = request.headers.get("X-Correlation-ID")
    return header_value if header_value else str(uuid4())


async def _get_session_or_404(session: AsyncSession, tenant_id: UUID, session_id: UUID) -> ClientSession:
    client_session = await session.scalar(
        select(ClientSession)
        .options(selectinload(ClientSession.goal))
        .where(ClientSession.id == session_id, ClientSession.tenant_id == tenant_id)
    )
    if client_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return client_session


def _consent_denied(exc: ConsentRequiredError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.public_detail)


@router.post("", operation_id="createSession", response_model=SessionResponse, status_code=201)
async def create_session(
    payload: SessionCreateRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> ClientSession:
    """Start a minimal session for a tenant-owned client with active analysis consent."""
    client_exists = await session.scalar(
        select(ClientProfile.id).where(ClientProfile.id == payload.client_id, ClientProfile.tenant_id == context.tenant_id)
    )
    if client_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    try:
        await ConsentService(session).assert_analysis_allowed(tenant_id=context.tenant_id, client_id=payload.client_id)
    except ConsentRequiredError as exc:
        raise _consent_denied(exc) from exc

    goal = SessionGoal(
        tenant_id=context.tenant_id,
        client_id=payload.client_id,
        title=payload.goal.title,
        description=payload.goal.description,
        created_by_user_id=context.principal.user_id,
    )
    session.add(goal)
    await session.flush()

    client_session = ClientSession(
        tenant_id=context.tenant_id,
        client_id=payload.client_id,
        goal_id=goal.id,
        status=SessionStatus.ACTIVE,
        created_by_user_id=context.principal.user_id,
        updated_by_user_id=context.principal.user_id,
    )
    session.add(client_session)
    await session.flush()
    await AuditService(session).append(
        tenant_id=context.tenant_id,
        actor_user_id=context.principal.user_id,
        action=AuditAction.SESSION_START,
        resource_type="session",
        resource_id=str(client_session.id),
        reason="session_started",
        correlation_id=_correlation_id(request),
        metadata_json={"client_id": str(payload.client_id), "status": SessionStatus.ACTIVE.value},
    )
    await session.commit()
    return await _get_session_or_404(session, context.tenant_id, client_session.id)


@router.get("", operation_id="listSessions", response_model=SessionListResponse)
async def list_sessions(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    client_id: Annotated[UUID | None, Query()] = None,
    status_filter: Annotated[SessionStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SessionListResponse:
    """List sessions for the authenticated tenant only."""
    statement = select(ClientSession).options(selectinload(ClientSession.goal)).where(ClientSession.tenant_id == context.tenant_id)
    if client_id is not None:
        statement = statement.where(ClientSession.client_id == client_id)
    if status_filter is not None:
        statement = statement.where(ClientSession.status == status_filter)
    statement = statement.order_by(ClientSession.started_at.desc(), ClientSession.id).limit(limit).offset(offset)
    sessions = list((await session.execute(statement)).scalars().all())
    return SessionListResponse(items=[SessionResponse.model_validate(item) for item in sessions], limit=limit, offset=offset)


@router.get("/{session_id}", operation_id="getSession", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> ClientSession:
    """Return a tenant-owned session without exposing workflow or engine state."""
    return await _get_session_or_404(session, context.tenant_id, session_id)


@router.patch("/{session_id}/status", operation_id="updateSessionStatus", response_model=SessionResponse)
async def update_session_status(
    session_id: UUID,
    payload: SessionStatusUpdateRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
) -> ClientSession:
    """Move an active session to a terminal status without workflow side effects."""
    client_session = await _get_session_or_404(session, context.tenant_id, session_id)
    if client_session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is not active")
    if payload.status == SessionStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Terminal status required")

    client_session.status = payload.status
    client_session.ended_at = datetime.now(UTC)
    client_session.updated_by_user_id = context.principal.user_id
    await session.flush()
    await AuditService(session).append(
        tenant_id=context.tenant_id,
        actor_user_id=context.principal.user_id,
        action=AuditAction.SESSION_START,
        resource_type="session",
        resource_id=str(client_session.id),
        reason="session_status_updated",
        correlation_id=_correlation_id(request),
        metadata_json={"status": payload.status.value},
    )
    await session.commit()
    return await _get_session_or_404(session, context.tenant_id, client_session.id)
