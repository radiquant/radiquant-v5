"""radi144 materialized projection storage gate (ADR-0002)

Revision ID: 0008_module_projections
Revises: 0007_engine_result_storage
Create Date: 2026-05-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0008_module_projections"
down_revision = "0007_engine_result_storage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "module_projections",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("module_run_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("projection_kind", sa.String(length=40), nullable=False),
        sa.Column("projection_json", sa.JSON(), nullable=False),
        sa.Column("raw_debug_excluded", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role in ('client', 'therapist')", name=op.f("ck_module_projections_module_projections_role_allowed")),
        sa.CheckConstraint("raw_debug_excluded = true", name=op.f("ck_module_projections_module_projections_raw_debug_excluded")),
        sa.ForeignKeyConstraint(["module_run_id"], ["module_runs.id"], name=op.f("fk_module_projections_module_run_id_module_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_module_projections_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_module_projections")),
        sa.UniqueConstraint("tenant_id", "module_run_id", "role", name=op.f("uq_module_projections_tenant_run_role")),
    )
    op.create_index(op.f("ix_module_projections_module_run_id"), "module_projections", ["module_run_id"], unique=False)
    op.create_index(op.f("ix_module_projections_tenant_id"), "module_projections", ["tenant_id"], unique=False)
    op.create_index("ix_module_projections_tenant_run", "module_projections", ["tenant_id", "module_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_module_projections_tenant_run", table_name="module_projections")
    op.drop_index(op.f("ix_module_projections_tenant_id"), table_name="module_projections")
    op.drop_index(op.f("ix_module_projections_module_run_id"), table_name="module_projections")
    op.drop_table("module_projections")
