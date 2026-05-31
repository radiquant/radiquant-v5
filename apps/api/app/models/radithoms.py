"""RadiThoms result storage ORM models."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin


class RadiThomsResult(TimestampMixin, Base):
    """Tenant-scoped sensitive RadiThoms result payload."""

    __tablename__ = "radithoms_results"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    module_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("module_runs.id", ondelete="CASCADE"), primary_key=True
    )
    schema_id: Mapped[str] = mapped_column(String(120), nullable=False)
    result_payload_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    projection_status: Mapped[str] = mapped_column(
        String(80), nullable=False, default="pending_projection_builder"
    )

    __table_args__ = (
        CheckConstraint("schema_id = 'radithoms_result_v1'", name="radithoms_results_schema_v1"),
        CheckConstraint(
            "projection_status = 'pending_projection_builder'",
            name="radithoms_results_projection_pending",
        ),
        Index("ix_radithoms_results_tenant_run", "tenant_id", "module_run_id"),
    )
