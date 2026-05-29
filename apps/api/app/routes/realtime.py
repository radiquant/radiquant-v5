"""Tenant-scoped Realtime API Gate routes.

Scope: replay/fallback polling plus finite SSE replay from the durable event log.
Workflow UI, job tracker runtime, and engine execution remain blocked.
"""

from collections.abc import AsyncIterator
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.event import EventRecord
from app.models.session import ClientSession
from app.schemas.realtime import EventReplayItem, EventReplayResponse
from app.security.tenant_guard import TenantContext, require_tenant_context

router = APIRouter(tags=["realtime"])


async def _get_session_or_404(session: AsyncSession, tenant_id: UUID, session_id: UUID) -> ClientSession:
    client_session = await session.scalar(select(ClientSession).where(ClientSession.id == session_id, ClientSession.tenant_id == tenant_id))
    if client_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return client_session


async def _get_cursor_or_422(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    session_id: UUID,
    after_event_id: UUID | None,
) -> EventRecord | None:
    if after_event_id is None:
        return None
    cursor = await session.scalar(
        select(EventRecord).where(
            EventRecord.tenant_id == tenant_id,
            EventRecord.session_id == session_id,
            EventRecord.event_id == after_event_id,
        )
    )
    if cursor is None:
        raise HTTPException(status_code=422, detail="Invalid replay cursor")
    return cursor


def _event_statement(
    *,
    tenant_id: UUID,
    session_id: UUID,
    cursor: EventRecord | None,
    limit: int,
) -> Select[tuple[EventRecord]]:
    statement = select(EventRecord).where(EventRecord.tenant_id == tenant_id, EventRecord.session_id == session_id)
    if cursor is not None:
        statement = statement.where(
            or_(
                EventRecord.occurred_at > cursor.occurred_at,
                (EventRecord.occurred_at == cursor.occurred_at) & (EventRecord.id > cursor.id),
            )
        )
    return statement.order_by(EventRecord.occurred_at, EventRecord.id).limit(limit)


def _project_event(record: EventRecord) -> EventReplayItem:
    return EventReplayItem(
        event_id=record.event_id,
        event_type=record.event_type,
        occurred_at=record.occurred_at,
        tenant_id=record.tenant_id,
        correlation_id=record.correlation_id,
        session_id=record.session_id,
        workflow_run_id=record.workflow_run_id,
        workflow_step_run_id=record.workflow_step_run_id,
        resource_type=record.resource_type,
        resource_id=record.resource_id,
        payload=record.payload_json,
    )


async def _load_events(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    session_id: UUID,
    after_event_id: UUID | None,
    limit: int,
) -> tuple[list[EventReplayItem], UUID | None]:
    await _get_session_or_404(session, tenant_id, session_id)
    cursor = await _get_cursor_or_422(session, tenant_id=tenant_id, session_id=session_id, after_event_id=after_event_id)
    records = list((await session.execute(_event_statement(tenant_id=tenant_id, session_id=session_id, cursor=cursor, limit=limit))).scalars().all())
    items = [_project_event(record) for record in records]
    next_cursor = items[-1].event_id if items else after_event_id
    return items, next_cursor


@router.get(
    "/sessions/{session_id}/events",
    operation_id="listSessionEvents",
    response_model=EventReplayResponse,
)
async def list_session_events(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    after_event_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> EventReplayResponse:
    """Replay tenant-scoped session events for explicit fallback polling."""
    items, next_cursor = await _load_events(
        session,
        tenant_id=context.tenant_id,
        session_id=session_id,
        after_event_id=after_event_id,
        limit=limit,
    )
    return EventReplayResponse(items=items, limit=limit, after_event_id=after_event_id, next_cursor=next_cursor)


@router.get("/sessions/{session_id}/events/stream", operation_id="streamSessionEvents")
async def stream_session_events(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    after_event_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> StreamingResponse:
    """Return a finite SSE replay batch from the event log.

    This is intentionally not a job tracker and does not synthesize progress.
    """
    items, _next_cursor = await _load_events(
        session,
        tenant_id=context.tenant_id,
        session_id=session_id,
        after_event_id=after_event_id,
        limit=limit,
    )

    async def event_stream() -> AsyncIterator[str]:
        for item in items:
            payload = item.model_dump(mode="json")
            yield f"id: {item.event_id}\nevent: {item.event_type}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
