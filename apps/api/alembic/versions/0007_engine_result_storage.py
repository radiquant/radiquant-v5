"""engine result storage gate

Revision ID: 0007_engine_result_storage
Revises: 0006_event_schema_gate
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0007_engine_result_storage"
down_revision = "0006_event_schema_gate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "module_runs",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_step_run_id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.String(length=80), nullable=False),
        sa.Column("phase", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("schema_id", sa.String(length=120), nullable=False),
        sa.Column("job_contract_schema_id", sa.String(length=120), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(module_id) >= 1", name=op.f("ck_module_runs_module_runs_module_id_min_length")),
        sa.CheckConstraint("status in ('queued', 'storage_ready', 'result_stored', 'failed_closed')", name=op.f("ck_module_runs_module_runs_status_allowed")),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], name=op.f("fk_module_runs_session_id_sessions"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_module_runs_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], name=op.f("fk_module_runs_workflow_run_id_workflow_runs"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workflow_step_run_id"], ["workflow_step_runs.id"], name=op.f("fk_module_runs_workflow_step_run_id_workflow_step_runs"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_module_runs")),
        sa.UniqueConstraint("workflow_step_run_id", "module_id", name=op.f("uq_module_runs_workflow_step_run_id_module_id")),
    )
    op.create_index(op.f("ix_module_runs_module_id"), "module_runs", ["module_id"], unique=False)
    op.create_index(op.f("ix_module_runs_phase"), "module_runs", ["phase"], unique=False)
    op.create_index(op.f("ix_module_runs_session_id"), "module_runs", ["session_id"], unique=False)
    op.create_index(op.f("ix_module_runs_status"), "module_runs", ["status"], unique=False)
    op.create_index(op.f("ix_module_runs_tenant_id"), "module_runs", ["tenant_id"], unique=False)
    op.create_index("ix_module_runs_tenant_module", "module_runs", ["tenant_id", "module_id"], unique=False)
    op.create_index("ix_module_runs_tenant_session", "module_runs", ["tenant_id", "session_id"], unique=False)
    op.create_index("ix_module_runs_tenant_workflow", "module_runs", ["tenant_id", "workflow_run_id"], unique=False)
    op.create_index(op.f("ix_module_runs_workflow_run_id"), "module_runs", ["workflow_run_id"], unique=False)
    op.create_index(op.f("ix_module_runs_workflow_step_run_id"), "module_runs", ["workflow_step_run_id"], unique=False)

    op.create_table(
        "module_results",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("module_run_id", sa.Uuid(), nullable=False),
        sa.Column("schema_id", sa.String(length=120), nullable=False),
        sa.Column("result_payload_json", sa.JSON(), nullable=False),
        sa.Column("retention_json", sa.JSON(), nullable=False),
        sa.Column("projection_status", sa.String(length=80), nullable=False),
        sa.Column("raw_debug_allowed", sa.Boolean(), nullable=False),
        sa.Column("client_projection_required", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("schema_id = 'radi144_result_v1'", name=op.f("ck_module_results_module_results_schema_radi144_v1")),
        sa.CheckConstraint("projection_status = 'pending_projection_builder'", name=op.f("ck_module_results_module_results_projection_pending")),
        sa.CheckConstraint("raw_debug_allowed = false", name=op.f("ck_module_results_module_results_raw_debug_forbidden")),
        sa.CheckConstraint("client_projection_required = true", name=op.f("ck_module_results_module_results_projection_required")),
        sa.ForeignKeyConstraint(["module_run_id"], ["module_runs.id"], name=op.f("fk_module_results_module_run_id_module_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_module_results_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_module_results")),
        sa.UniqueConstraint("module_run_id", name=op.f("uq_module_results_module_run_id")),
    )
    op.create_index(op.f("ix_module_results_module_run_id"), "module_results", ["module_run_id"], unique=False)
    op.create_index(op.f("ix_module_results_tenant_id"), "module_results", ["tenant_id"], unique=False)
    op.create_index("ix_module_results_tenant_schema", "module_results", ["tenant_id", "schema_id"], unique=False)

    op.create_table(
        "module_provenances",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("module_run_id", sa.Uuid(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=80), nullable=False),
        sa.Column("manifest_version", sa.String(length=80), nullable=False),
        sa.Column("input_hash", sa.String(length=128), nullable=False),
        sa.Column("reference_matrix_version", sa.String(length=80), nullable=False),
        sa.Column("compute_backend", sa.String(length=80), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("provenance_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(algorithm_version) >= 1", name=op.f("ck_module_provenances_module_provenances_algorithm_version_min_length")),
        sa.CheckConstraint("length(manifest_version) >= 1", name=op.f("ck_module_provenances_module_provenances_manifest_version_min_length")),
        sa.CheckConstraint("duration_ms >= 0", name=op.f("ck_module_provenances_module_provenances_duration_non_negative")),
        sa.ForeignKeyConstraint(["module_run_id"], ["module_runs.id"], name=op.f("fk_module_provenances_module_run_id_module_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_module_provenances_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_module_provenances")),
        sa.UniqueConstraint("module_run_id", name=op.f("uq_module_provenances_module_run_id")),
    )
    op.create_index(op.f("ix_module_provenances_module_run_id"), "module_provenances", ["module_run_id"], unique=False)
    op.create_index(op.f("ix_module_provenances_tenant_id"), "module_provenances", ["tenant_id"], unique=False)
    op.create_index("ix_module_provenances_tenant_run", "module_provenances", ["tenant_id", "module_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_module_provenances_tenant_run", table_name="module_provenances")
    op.drop_index(op.f("ix_module_provenances_tenant_id"), table_name="module_provenances")
    op.drop_index(op.f("ix_module_provenances_module_run_id"), table_name="module_provenances")
    op.drop_table("module_provenances")

    op.drop_index("ix_module_results_tenant_schema", table_name="module_results")
    op.drop_index(op.f("ix_module_results_tenant_id"), table_name="module_results")
    op.drop_index(op.f("ix_module_results_module_run_id"), table_name="module_results")
    op.drop_table("module_results")

    op.drop_index(op.f("ix_module_runs_workflow_step_run_id"), table_name="module_runs")
    op.drop_index(op.f("ix_module_runs_workflow_run_id"), table_name="module_runs")
    op.drop_index("ix_module_runs_tenant_workflow", table_name="module_runs")
    op.drop_index("ix_module_runs_tenant_session", table_name="module_runs")
    op.drop_index("ix_module_runs_tenant_module", table_name="module_runs")
    op.drop_index(op.f("ix_module_runs_tenant_id"), table_name="module_runs")
    op.drop_index(op.f("ix_module_runs_status"), table_name="module_runs")
    op.drop_index(op.f("ix_module_runs_session_id"), table_name="module_runs")
    op.drop_index(op.f("ix_module_runs_phase"), table_name="module_runs")
    op.drop_index(op.f("ix_module_runs_module_id"), table_name="module_runs")
    op.drop_table("module_runs")
