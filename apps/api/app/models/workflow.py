"""Tenant-scoped workflow planning ORM models.

Workflow API Gate scope: create a manifest-derived plan only. Realtime,
engine execution, module results, and raw/debug output remain blocked.
"""

import enum
from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowRunStatus(str, enum.Enum):
    """Lifecycle for a workflow run before execution gates open."""

    PLANNED = "planned"
    CANCELLED = "cancelled"


class WorkflowStepRunStatus(str, enum.Enum):
    """Lifecycle for manifest-derived workflow step runs before execution gates open."""

    PLANNED = "planned"
    BLOCKED = "blocked"


class WorkflowRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant-scoped workflow plan derived from the workflow manifest."""

    __tablename__ = "workflow_runs"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workflow_id: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    workflow_slug: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[WorkflowRunStatus] = mapped_column(
        Enum(WorkflowRunStatus, name="workflow_run_status"),
        nullable=False,
        default=WorkflowRunStatus.PLANNED,
        index=True,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    steps: Mapped[list["WorkflowStepRun"]] = relationship(
        back_populates="workflow_run",
        cascade="all, delete-orphan",
        order_by="WorkflowStepRun.step_index",
    )

    __table_args__ = (
        CheckConstraint("length(workflow_id) >= 1", name="workflow_run_workflow_id_min_length"),
        Index("ix_workflow_runs_tenant_session", "tenant_id", "session_id"),
        Index("ix_workflow_runs_tenant_status", "tenant_id", "status"),
    )


class WorkflowStepRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Manifest-derived planned step for a workflow run."""

    __tablename__ = "workflow_step_runs"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workflow_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    module_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    phase: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[WorkflowStepRunStatus] = mapped_column(
        Enum(WorkflowStepRunStatus, name="workflow_step_run_status"),
        nullable=False,
        default=WorkflowStepRunStatus.PLANNED,
        index=True,
    )

    workflow_run: Mapped[WorkflowRun] = relationship(back_populates="steps")

    __table_args__ = (
        CheckConstraint("step_index >= 0", name="workflow_step_run_index_non_negative"),
        UniqueConstraint("workflow_run_id", "step_index", name="uq_workflow_step_runs_workflow_run_id_step_index"),
        Index("ix_workflow_step_runs_tenant_run", "tenant_id", "workflow_run_id"),
    )
