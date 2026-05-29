"""Audit append service.

Audit records are event-truth artifacts: services append new events and never mutate
existing audit rows.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog


class AuditService:
    """Append-only audit event writer."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(
        self,
        *,
        tenant_id: UUID,
        action: AuditAction,
        resource_type: str,
        correlation_id: str,
        actor_user_id: UUID | None = None,
        resource_id: str | None = None,
        reason: str = "",
        metadata_json: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Append an audit event to the current unit of work."""
        audit_log = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            metadata_json=metadata_json or {},
            correlation_id=correlation_id,
        )
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log
