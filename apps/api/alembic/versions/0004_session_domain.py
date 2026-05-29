"""session domain baseline

Revision ID: 0004_session_domain
Revises: 0003_client_profile_consent
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_session_domain"
down_revision = "0003_client_profile_consent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_goals",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(title) >= 1", name=op.f("ck_session_goals_session_goal_title_min_length")),
        sa.ForeignKeyConstraint(["client_id"], ["client_profiles.id"], name=op.f("fk_session_goals_client_id_client_profiles"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_session_goals_created_by_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_session_goals_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_goals")),
    )
    op.create_index(op.f("ix_session_goals_client_id"), "session_goals", ["client_id"], unique=False)
    op.create_index(op.f("ix_session_goals_created_by_user_id"), "session_goals", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_session_goals_tenant_id"), "session_goals", ["tenant_id"], unique=False)
    op.create_index("ix_session_goals_tenant_client", "session_goals", ["tenant_id", "client_id"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "COMPLETED", "CANCELLED", name="session_status"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["client_profiles.id"], name=op.f("fk_sessions_client_id_client_profiles"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_sessions_created_by_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["goal_id"], ["session_goals.id"], name=op.f("fk_sessions_goal_id_session_goals"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_sessions_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], name=op.f("fk_sessions_updated_by_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
    )
    op.create_index(op.f("ix_sessions_client_id"), "sessions", ["client_id"], unique=False)
    op.create_index(op.f("ix_sessions_created_by_user_id"), "sessions", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_sessions_goal_id"), "sessions", ["goal_id"], unique=False)
    op.create_index(op.f("ix_sessions_status"), "sessions", ["status"], unique=False)
    op.create_index(op.f("ix_sessions_tenant_id"), "sessions", ["tenant_id"], unique=False)
    op.create_index("ix_sessions_tenant_client", "sessions", ["tenant_id", "client_id"], unique=False)
    op.create_index("ix_sessions_tenant_status", "sessions", ["tenant_id", "status"], unique=False)
    op.create_index(op.f("ix_sessions_updated_by_user_id"), "sessions", ["updated_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sessions_updated_by_user_id"), table_name="sessions")
    op.drop_index("ix_sessions_tenant_status", table_name="sessions")
    op.drop_index("ix_sessions_tenant_client", table_name="sessions")
    op.drop_index(op.f("ix_sessions_tenant_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_status"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_goal_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_created_by_user_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_client_id"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_session_goals_tenant_client", table_name="session_goals")
    op.drop_index(op.f("ix_session_goals_tenant_id"), table_name="session_goals")
    op.drop_index(op.f("ix_session_goals_created_by_user_id"), table_name="session_goals")
    op.drop_index(op.f("ix_session_goals_client_id"), table_name="session_goals")
    op.drop_table("session_goals")
    op.execute("DROP TYPE IF EXISTS session_status")
