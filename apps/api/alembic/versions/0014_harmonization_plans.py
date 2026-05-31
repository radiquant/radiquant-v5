"""harmonization plan approval gate

Revision ID: 0014_harmonization_plans
Revises: 0013_radicopen_results
Create Date: 2026-05-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_harmonization_plans"
down_revision = "0013_radicopen_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "harmonization_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("plan_payload_json", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('draft', 'approved')",
            name=op.f("ck_harmonization_plans_status_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            name=op.f("fk_harmonization_plans_approved_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_harmonization_plans_created_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name=op.f("fk_harmonization_plans_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_harmonization_plans_tenant_id_tenants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_harmonization_plans")),
    )
    op.create_index(
        op.f("ix_harmonization_plans_tenant_id"),
        "harmonization_plans",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_harmonization_plans_tenant_session",
        "harmonization_plans",
        ["tenant_id", "session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_harmonization_plans_tenant_session", table_name="harmonization_plans")
    op.drop_index(op.f("ix_harmonization_plans_tenant_id"), table_name="harmonization_plans")
    op.drop_table("harmonization_plans")
