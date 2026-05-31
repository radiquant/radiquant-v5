"""radithoms result storage scaffold (ADR-0003)

Revision ID: 0012_radithoms_results
Revises: 0011_radiblohm_results
Create Date: 2026-05-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_radithoms_results"
down_revision = "0011_radiblohm_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radithoms_results",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("module_run_id", sa.Uuid(), nullable=False),
        sa.Column("schema_id", sa.String(length=120), nullable=False),
        sa.Column("result_payload_json", sa.JSON(), nullable=False),
        sa.Column("projection_status", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "schema_id = 'radithoms_result_v1'",
            name=op.f("ck_radithoms_results_radithoms_results_schema_v1"),
        ),
        sa.CheckConstraint(
            "projection_status = 'pending_projection_builder'",
            name=op.f("ck_radithoms_results_radithoms_results_projection_pending"),
        ),
        sa.ForeignKeyConstraint(
            ["module_run_id"],
            ["module_runs.id"],
            name=op.f("fk_radithoms_results_module_run_id_module_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_radithoms_results_tenant_id_tenants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("module_run_id", name=op.f("pk_radithoms_results")),
    )
    op.create_index(
        op.f("ix_radithoms_results_tenant_id"),
        "radithoms_results",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_radithoms_results_tenant_run",
        "radithoms_results",
        ["tenant_id", "module_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_radithoms_results_tenant_run", table_name="radithoms_results")
    op.drop_index(op.f("ix_radithoms_results_tenant_id"), table_name="radithoms_results")
    op.drop_table("radithoms_results")
