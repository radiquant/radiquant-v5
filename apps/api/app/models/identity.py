"""Identity and tenant ORM models for the v5 security core."""

import enum
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RoleName(str, enum.Enum):
    """Canonical v5 roles."""

    ADMIN = "admin"
    THERAPIST = "therapist"
    ASSISTANT = "assistant"
    CLIENT = "client"
    RESEARCHER = "researcher"
    SYSTEM = "system"


class TenantStatus(str, enum.Enum):
    """Tenant lifecycle states."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class UserStatus(str, enum.Enum):
    """User lifecycle states."""

    ACTIVE = "active"
    INVITED = "invited"
    DISABLED = "disabled"


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant boundary for every client/session/result resource."""

    __tablename__ = "tenants"

    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, name="tenant_status"), nullable=False, default=TenantStatus.ACTIVE
    )

    users: Mapped[list["User"]] = relationship(back_populates="tenant")

    __table_args__ = (
        CheckConstraint("length(slug) >= 3", name="tenant_slug_min_length"),
    )


class Role(UUIDPrimaryKeyMixin, Base):
    """RBAC role catalog."""

    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(Enum(RoleName, name="role_name"), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False, default="")

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant-scoped user account.

    Password hashing/session implementation is intentionally not added yet; this model
    establishes the security and tenant boundary for the next Auth Core step.
    """

    __tablename__ = "users"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    role_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"), nullable=False, default=UserStatus.INVITED
    )
    is_mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    tenant: Mapped[Tenant] = relationship(back_populates="users")
    role: Mapped[Role] = relationship(back_populates="users")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_id_email"),
        Index("ix_users_tenant_role", "tenant_id", "role_id"),
    )
