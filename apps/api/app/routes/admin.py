"""Tenant-scoped admin routes."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.audit import AuditLog
from app.models.client import ClientProfile
from app.models.identity import RoleName
from app.models.session import ClientSession, SessionStatus
from app.schemas.admin import AdminStatsResponse, AuditLogEntry
from app.security.tenant_guard import TenantContext, require_tenant_context

admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _require_admin(context: TenantContext) -> None:
    if context.principal.role is not RoleName.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )


@admin_router.get(
    "/audit-log",
    operation_id="listAdminAuditLog",
    response_model=list[AuditLogEntry],
)
async def list_admin_audit_log(
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AuditLogEntry]:
    """Return the latest tenant-scoped audit-log entries for admins."""
    _require_admin(context)
    statement = (
        select(AuditLog)
        .where(AuditLog.tenant_id == context.tenant_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(100)
    )
    rows = list((await session.execute(statement)).scalars().all())
    return [
        AuditLogEntry(
            timestamp=row.created_at,
            action=row.action.value,
            user_id=row.actor_user_id,
            tenant_id=row.tenant_id,
            details=row.metadata_json,
        )
        for row in rows
    ]


@admin_router.get(
    "/stats",
    operation_id="getAdminStats",
    response_model=AdminStatsResponse,
)
async def get_admin_stats(
    context: Annotated[TenantContext, Depends(require_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminStatsResponse:
    """Return tenant-scoped aggregate counters for admins."""
    _require_admin(context)
    since = datetime.now(UTC) - timedelta(hours=24)
    total_sessions = await session.scalar(
        select(func.count()).select_from(ClientSession).where(
            ClientSession.tenant_id == context.tenant_id
        )
    )
    total_clients = await session.scalar(
        select(func.count()).select_from(ClientProfile).where(
            ClientProfile.tenant_id == context.tenant_id
        )
    )
    active_sessions_24h = await session.scalar(
        select(func.count()).select_from(ClientSession).where(
            ClientSession.tenant_id == context.tenant_id,
            ClientSession.status == SessionStatus.ACTIVE,
            ClientSession.started_at >= since,
        )
    )
    return AdminStatsResponse(
        total_sessions=int(total_sessions or 0),
        total_clients=int(total_clients or 0),
        active_sessions_24h=int(active_sessions_24h or 0),
    )
