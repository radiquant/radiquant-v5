"""Tenant-scoped event-truth ORM models.

Event Schema Gate scope: persist schema-validated event envelopes for later
replay/realtime gates. No streaming, polling endpoint, job execution, or engine
progress logic is opened here.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class EventRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Durable tenant-scoped event envelope validated against the event registry."""

    __tablename__ = "event_records"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    event_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    session_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    workflow_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    workflow_step_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workflow_step_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resource_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_event_records_tenant_occurred", "tenant_id", "occurred_at"),
        Index("ix_event_records_tenant_type", "tenant_id", "event_type"),
        Index("ix_event_records_tenant_session", "tenant_id", "session_id"),
        Index("ix_event_records_tenant_workflow", "tenant_id", "workflow_run_id"),
    )
