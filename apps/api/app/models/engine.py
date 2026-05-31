"""Engine result storage ORM models.

Radi144 Result Persistence Storage Gate scope: define tenant-scoped storage
entities for ModuleRun, ModuleResult, and ModuleProvenance. This module does
not start workers, build projections, or execute engines.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ModuleRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant-scoped storage anchor for a module run lifecycle."""

    __tablename__ = "module_runs"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workflow_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workflow_step_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workflow_step_runs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    module_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    phase: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="storage_ready", index=True)
    schema_id: Mapped[str] = mapped_column(String(120), nullable=False)
    job_contract_schema_id: Mapped[str] = mapped_column(String(120), nullable=False)

    result: Mapped[ModuleResult | None] = relationship(back_populates="module_run", cascade="all, delete-orphan")
    provenance: Mapped[ModuleProvenance | None] = relationship(back_populates="module_run", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("length(module_id) >= 1", name="module_runs_module_id_min_length"),
        CheckConstraint("status in ('queued', 'storage_ready', 'result_stored', 'failed_closed')", name="module_runs_status_allowed"),
        UniqueConstraint("workflow_step_run_id", "module_id", name="uq_module_runs_workflow_step_run_id_module_id"),
        Index("ix_module_runs_tenant_session", "tenant_id", "session_id"),
        Index("ix_module_runs_tenant_workflow", "tenant_id", "workflow_run_id"),
        Index("ix_module_runs_tenant_module", "tenant_id", "module_id"),
    )


class ModuleResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant-scoped sensitive result payload with retention and projection metadata."""

    __tablename__ = "module_results"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    module_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("module_runs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    schema_id: Mapped[str] = mapped_column(String(120), nullable=False)
    result_payload_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    retention_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    projection_status: Mapped[str] = mapped_column(String(80), nullable=False, default="pending_projection_builder")
    raw_debug_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    client_projection_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    module_run: Mapped[ModuleRun] = relationship(back_populates="result")

    __table_args__ = (
        CheckConstraint("schema_id = 'radi144_result_v1'", name="module_results_schema_radi144_v1"),
        CheckConstraint("projection_status = 'pending_projection_builder'", name="module_results_projection_pending"),
        CheckConstraint("raw_debug_allowed = false", name="module_results_raw_debug_forbidden"),
        CheckConstraint("client_projection_required = true", name="module_results_projection_required"),
        Index("ix_module_results_tenant_schema", "tenant_id", "schema_id"),
    )


class ModuleProvenance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Reproducibility metadata for a stored module result."""

    __tablename__ = "module_provenances"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    module_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("module_runs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    algorithm_version: Mapped[str] = mapped_column(String(80), nullable=False)
    manifest_version: Mapped[str] = mapped_column(String(80), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    reference_matrix_version: Mapped[str] = mapped_column(String(80), nullable=False)
    compute_backend: Mapped[str] = mapped_column(String(80), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provenance_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)

    module_run: Mapped[ModuleRun] = relationship(back_populates="provenance")

    __table_args__ = (
        CheckConstraint("length(algorithm_version) >= 1", name="module_provenances_algorithm_version_min_length"),
        CheckConstraint("length(manifest_version) >= 1", name="module_provenances_manifest_version_min_length"),
        CheckConstraint("duration_ms >= 0", name="module_provenances_duration_non_negative"),
        Index("ix_module_provenances_tenant_run", "tenant_id", "module_run_id"),
    )


class ModuleProjection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tenant-scoped materialized Radi144 role projection (ADR-0002)."""

    __tablename__ = "module_projections"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    module_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("module_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    projection_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    projection_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    raw_debug_excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("role in ('client', 'therapist')", name="module_projections_role_allowed"),
        CheckConstraint("raw_debug_excluded = true", name="module_projections_raw_debug_excluded"),
        UniqueConstraint("tenant_id", "module_run_id", "role", name="uq_module_projections_tenant_run_role"),
        Index("ix_module_projections_tenant_run", "tenant_id", "module_run_id"),
    )
