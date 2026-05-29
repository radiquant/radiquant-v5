"""workflow api gate planning tables

Revision ID: 0005_workflow_api_gate
Revises: 0004_session_domain
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_workflow_api_gate"
down_revision = "0004_session_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_runs",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.String(length=16), nullable=False),
        sa.Column("workflow_slug", sa.String(length=120), nullable=False),
        sa.Column("status", sa.Enum("PLANNED", "CANCELLED", name="workflow_run_status"), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(workflow_id) >= 1", name=op.f("ck_workflow_runs_workflow_run_workflow_id_min_length")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_workflow_runs_created_by_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], name=op.f("fk_workflow_runs_session_id_sessions"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_workflow_runs_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], name=op.f("fk_workflow_runs_updated_by_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow_runs")),
    )
    op.create_index(op.f("ix_workflow_runs_created_by_user_id"), "workflow_runs", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_workflow_runs_session_id"), "workflow_runs", ["session_id"], unique=False)
    op.create_index(op.f("ix_workflow_runs_status"), "workflow_runs", ["status"], unique=False)
    op.create_index(op.f("ix_workflow_runs_tenant_id"), "workflow_runs", ["tenant_id"], unique=False)
    op.create_index("ix_workflow_runs_tenant_session", "workflow_runs", ["tenant_id", "session_id"], unique=False)
    op.create_index("ix_workflow_runs_tenant_status", "workflow_runs", ["tenant_id", "status"], unique=False)
    op.create_index(op.f("ix_workflow_runs_updated_by_user_id"), "workflow_runs", ["updated_by_user_id"], unique=False)
    op.create_index(op.f("ix_workflow_runs_workflow_id"), "workflow_runs", ["workflow_id"], unique=False)

    op.create_table(
        "workflow_step_runs",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.String(length=80), nullable=False),
        sa.Column("phase", sa.String(length=40), nullable=False),
        sa.Column("status", sa.Enum("PLANNED", "BLOCKED", name="workflow_step_run_status"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("step_index >= 0", name=op.f("ck_workflow_step_runs_workflow_step_run_index_non_negative")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_workflow_step_runs_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], name=op.f("fk_workflow_step_runs_workflow_run_id_workflow_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow_step_runs")),
        sa.UniqueConstraint("workflow_run_id", "step_index", name=op.f("uq_workflow_step_runs_workflow_run_id_step_index")),
    )
    op.create_index(op.f("ix_workflow_step_runs_module_id"), "workflow_step_runs", ["module_id"], unique=False)
    op.create_index(op.f("ix_workflow_step_runs_phase"), "workflow_step_runs", ["phase"], unique=False)
    op.create_index(op.f("ix_workflow_step_runs_status"), "workflow_step_runs", ["status"], unique=False)
    op.create_index(op.f("ix_workflow_step_runs_tenant_id"), "workflow_step_runs", ["tenant_id"], unique=False)
    op.create_index("ix_workflow_step_runs_tenant_run", "workflow_step_runs", ["tenant_id", "workflow_run_id"], unique=False)
    op.create_index(op.f("ix_workflow_step_runs_workflow_run_id"), "workflow_step_runs", ["workflow_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_step_runs_workflow_run_id"), table_name="workflow_step_runs")
    op.drop_index("ix_workflow_step_runs_tenant_run", table_name="workflow_step_runs")
    op.drop_index(op.f("ix_workflow_step_runs_tenant_id"), table_name="workflow_step_runs")
    op.drop_index(op.f("ix_workflow_step_runs_status"), table_name="workflow_step_runs")
    op.drop_index(op.f("ix_workflow_step_runs_phase"), table_name="workflow_step_runs")
    op.drop_index(op.f("ix_workflow_step_runs_module_id"), table_name="workflow_step_runs")
    op.drop_table("workflow_step_runs")
    op.drop_index(op.f("ix_workflow_runs_workflow_id"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_updated_by_user_id"), table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_tenant_status", table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_tenant_session", table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_tenant_id"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_status"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_session_id"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_created_by_user_id"), table_name="workflow_runs")
    op.drop_table("workflow_runs")
    op.execute("DROP TYPE IF EXISTS workflow_step_run_status")
    op.execute("DROP TYPE IF EXISTS workflow_run_status")
