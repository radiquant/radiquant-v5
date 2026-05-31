"""harmonization job pause resume stop gate

Revision ID: 0015_harmonization_jobs
Revises: 0014_harmonization_plans
Create Date: 2026-05-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015_harmonization_jobs"
down_revision = "0014_harmonization_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "harmonization_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="queued", nullable=False),
        sa.Column("hardware_ack", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('queued', 'running', 'paused', 'completed', 'failed', 'cancelled')",
            name=op.f("ck_harmonization_jobs_status_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["harmonization_plans.id"],
            name=op.f("fk_harmonization_jobs_plan_id_harmonization_plans"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_harmonization_jobs_tenant_id_tenants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_harmonization_jobs")),
    )
    op.create_index(
        op.f("ix_harmonization_jobs_tenant_id"),
        "harmonization_jobs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_harmonization_jobs_tenant_plan",
        "harmonization_jobs",
        ["tenant_id", "plan_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_harmonization_jobs_tenant_plan", table_name="harmonization_jobs")
    op.drop_index(op.f("ix_harmonization_jobs_tenant_id"), table_name="harmonization_jobs")
    op.drop_table("harmonization_jobs")
