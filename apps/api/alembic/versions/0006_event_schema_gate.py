"""event schema gate event records

Revision ID: 0006_event_schema_gate
Revises: 0005_workflow_api_gate
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_event_schema_gate"
down_revision = "0005_workflow_api_gate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_records",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.String(length=120), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_step_run_id", sa.Uuid(), nullable=True),
        sa.Column("resource_type", sa.String(length=120), nullable=True),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], name=op.f("fk_event_records_session_id_sessions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_event_records_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], name=op.f("fk_event_records_workflow_run_id_workflow_runs"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workflow_step_run_id"], ["workflow_step_runs.id"], name=op.f("fk_event_records_workflow_step_run_id_workflow_step_runs"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_records")),
        sa.UniqueConstraint("event_id", name=op.f("uq_event_records_event_id")),
    )
    op.create_index(op.f("ix_event_records_correlation_id"), "event_records", ["correlation_id"], unique=False)
    op.create_index(op.f("ix_event_records_event_id"), "event_records", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_records_event_type"), "event_records", ["event_type"], unique=False)
    op.create_index(op.f("ix_event_records_occurred_at"), "event_records", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_event_records_session_id"), "event_records", ["session_id"], unique=False)
    op.create_index(op.f("ix_event_records_tenant_id"), "event_records", ["tenant_id"], unique=False)
    op.create_index("ix_event_records_tenant_occurred", "event_records", ["tenant_id", "occurred_at"], unique=False)
    op.create_index("ix_event_records_tenant_session", "event_records", ["tenant_id", "session_id"], unique=False)
    op.create_index("ix_event_records_tenant_type", "event_records", ["tenant_id", "event_type"], unique=False)
    op.create_index("ix_event_records_tenant_workflow", "event_records", ["tenant_id", "workflow_run_id"], unique=False)
    op.create_index(op.f("ix_event_records_workflow_run_id"), "event_records", ["workflow_run_id"], unique=False)
    op.create_index(op.f("ix_event_records_workflow_step_run_id"), "event_records", ["workflow_step_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_event_records_workflow_step_run_id"), table_name="event_records")
    op.drop_index(op.f("ix_event_records_workflow_run_id"), table_name="event_records")
    op.drop_index("ix_event_records_tenant_workflow", table_name="event_records")
    op.drop_index("ix_event_records_tenant_type", table_name="event_records")
    op.drop_index("ix_event_records_tenant_session", table_name="event_records")
    op.drop_index("ix_event_records_tenant_occurred", table_name="event_records")
    op.drop_index(op.f("ix_event_records_tenant_id"), table_name="event_records")
    op.drop_index(op.f("ix_event_records_session_id"), table_name="event_records")
    op.drop_index(op.f("ix_event_records_occurred_at"), table_name="event_records")
    op.drop_index(op.f("ix_event_records_event_type"), table_name="event_records")
    op.drop_index(op.f("ix_event_records_event_id"), table_name="event_records")
    op.drop_index(op.f("ix_event_records_correlation_id"), table_name="event_records")
    op.drop_table("event_records")
