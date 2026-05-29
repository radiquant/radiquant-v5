"""Tenant-scoped client domain ORM models."""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class ClientStatus(str, enum.Enum):
    """Client profile lifecycle states."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class ConsentPurpose(str, enum.Enum):
    """Consent purposes required before sensitive processing."""

    ANALYSIS = "analysis"
    HARMONIZATION = "harmonization"
    TREND_ANALYSIS = "trend_analysis"
    REPORT_EXPORT = "report_export"
    REPLAY_RESEARCH_USE = "replay_research_use"
    HRV_PROCESSING = "hrv_processing"
    MEDIA_UPLOAD_PROCESSING = "media_upload_processing"


class ConsentStatus(str, enum.Enum):
    """Consent grant lifecycle states."""

    GRANTED = "granted"
    REVOKED = "revoked"


class ClientProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Human client profile owned by exactly one tenant."""

    __tablename__ = "client_profiles"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[ClientStatus] = mapped_column(
        Enum(ClientStatus, name="client_status"), nullable=False, default=ClientStatus.ACTIVE, index=True
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    consents: Mapped[list["ClientConsent"]] = relationship(back_populates="client")

    __table_args__ = (
        CheckConstraint("length(display_name) >= 1", name="client_display_name_min_length"),
        UniqueConstraint("tenant_id", "client_code", name="uq_client_profiles_tenant_id_client_code"),
        Index("ix_client_profiles_tenant_status", "tenant_id", "status"),
    )


class ClientConsent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Consent event for a tenant-scoped client and a specific processing purpose."""

    __tablename__ = "client_consents"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    client_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("client_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    purpose: Mapped[ConsentPurpose] = mapped_column(
        Enum(ConsentPurpose, name="consent_purpose"), nullable=False, index=True
    )
    status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus, name="consent_status"), nullable=False, default=ConsentStatus.GRANTED, index=True
    )
    consent_text_version: Mapped[str] = mapped_column(String(80), nullable=False)
    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped[ClientProfile] = relationship(back_populates="consents")

    __table_args__ = (
        Index("ix_client_consents_tenant_client", "tenant_id", "client_id"),
        Index("ix_client_consents_tenant_purpose_status", "tenant_id", "purpose", "status"),
    )
