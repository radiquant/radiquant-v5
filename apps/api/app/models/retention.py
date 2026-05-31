"""Retention policy ORM models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin, utc_now


class RetentionPolicy(UUIDPrimaryKeyMixin, Base):
    """Tenant-scoped retention cleanup policy."""

    __tablename__ = "retention_policies"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    data_type: Mapped[str] = mapped_column(String(40), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "data_type in ('sessions', 'events', 'module_results')",
            name="retention_policies_data_type_allowed",
        ),
        CheckConstraint("retention_days >= 1", name="retention_policies_retention_days_positive"),
        Index("ix_retention_policies_tenant_data_type", "tenant_id", "data_type"),
    )
