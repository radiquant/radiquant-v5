"""retention policy cleanup gate

Revision ID: 0016_retention_policy
Revises: 0015_harmonization_jobs
Create Date: 2026-05-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016_retention_policy"
down_revision = "0015_harmonization_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "retention_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("data_type", sa.String(length=40), nullable=False),
        sa.Column("retention_days", sa.Integer(), server_default="365", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "data_type in ('sessions', 'events', 'module_results')",
            name=op.f("ck_retention_policies_data_type_allowed"),
        ),
        sa.CheckConstraint(
            "retention_days >= 1",
            name=op.f("ck_retention_policies_retention_days_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_retention_policies_tenant_id_tenants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retention_policies")),
    )
    op.create_index(
        op.f("ix_retention_policies_tenant_id"),
        "retention_policies",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_retention_policies_tenant_data_type",
        "retention_policies",
        ["tenant_id", "data_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_retention_policies_tenant_data_type", table_name="retention_policies")
    op.drop_index(op.f("ix_retention_policies_tenant_id"), table_name="retention_policies")
    op.drop_table("retention_policies")
