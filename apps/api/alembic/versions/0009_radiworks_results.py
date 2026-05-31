"""radiworks result storage scaffold (ADR-0003)

Revision ID: 0009_radiworks_results
Revises: 0008_module_projections
Create Date: 2026-05-31
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0009_radiworks_results"
down_revision = "0008_module_projections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radiworks_results",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("module_run_id", sa.Uuid(), nullable=False),
        sa.Column("schema_id", sa.String(length=120), nullable=False),
        sa.Column("result_payload_json", sa.JSON(), nullable=False),
        sa.Column("projection_status", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "schema_id = 'radiworks_result_v1'",
            name=op.f("ck_radiworks_results_radiworks_results_schema_v1"),
        ),
        sa.CheckConstraint(
            "projection_status = 'pending_projection_builder'",
            name=op.f("ck_radiworks_results_radiworks_results_projection_pending"),
        ),
        sa.ForeignKeyConstraint(
            ["module_run_id"],
            ["module_runs.id"],
            name=op.f("fk_radiworks_results_module_run_id_module_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_radiworks_results_tenant_id_tenants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("module_run_id", name=op.f("pk_radiworks_results")),
    )
    op.create_index(
        op.f("ix_radiworks_results_tenant_id"),
        "radiworks_results",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_radiworks_results_tenant_run",
        "radiworks_results",
        ["tenant_id", "module_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_radiworks_results_tenant_run", table_name="radiworks_results")
    op.drop_index(op.f("ix_radiworks_results_tenant_id"), table_name="radiworks_results")
    op.drop_table("radiworks_results")
