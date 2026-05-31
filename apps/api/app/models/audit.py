"""Audit ORM model for the v5 compliance core."""

import enum
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditAction(str, enum.Enum):
    """Initial audit action catalog."""

    LOGIN_SECURITY_EVENT = "login_security_event"
    CLIENT_CREATE_UPDATE_DELETE = "client_create_update_delete"
    CONSENT_CHANGE = "consent_change"
    SESSION_START = "session_start"
    WORKFLOW_PLAN = "workflow_plan"
    ENGINE_RUN = "engine_run"
    HARMONIZATION_APPROVAL_JOB = "harmonization_approval_job"
    REPORT_EXPORT = "report_export"
    GDPR_EXPORT_DELETE_ANONYMIZE = "gdpr_export_delete_anonymize"
    ADMIN_CONFIG_CHANGE = "admin_config_change"


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant-scoped immutable audit event.

    Application services must append audit events; they must not update/delete existing events.
    Database-level immutability triggers can be added after the initial migration baseline.
    """

    __tablename__ = "audit_logs"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    correlation_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_logs_tenant_action_created", "tenant_id", "action", "created_at"),
    )
