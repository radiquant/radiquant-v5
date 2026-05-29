"""Tenant-scoped session domain ORM models.

This gate intentionally excludes WorkflowRun, workflow steps, realtime, and engine/module
fields. Those scopes open only after their own contract gates.
"""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class SessionStatus(str, enum.Enum):
    """Minimal lifecycle for a client session before workflow gates open."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant-scoped goal/intention for a client session."""

    __tablename__ = "session_goals"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    client_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("client_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    sessions: Mapped[list["ClientSession"]] = relationship(back_populates="goal")

    __table_args__ = (
        CheckConstraint("length(title) >= 1", name="session_goal_title_min_length"),
        Index("ix_session_goals_tenant_client", "tenant_id", "client_id"),
    )


class ClientSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Minimal tenant-scoped client session without workflow or engine state."""

    __tablename__ = "sessions"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    client_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("client_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    goal_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("session_goals.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"), nullable=False, default=SessionStatus.ACTIVE, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    goal: Mapped[SessionGoal] = relationship(back_populates="sessions")

    __table_args__ = (
        Index("ix_sessions_tenant_client", "tenant_id", "client_id"),
        Index("ix_sessions_tenant_status", "tenant_id", "status"),
    )
