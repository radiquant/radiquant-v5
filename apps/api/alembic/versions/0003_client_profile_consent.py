"""client profile and consent baseline

Revision ID: 0003_client_profile_consent
Revises: 0002_user_password_hash
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_client_profile_consent"
down_revision = "0002_user_password_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_profiles",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("client_code", sa.String(length=80), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "ARCHIVED", name="client_status"), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(display_name) >= 1", name=op.f("ck_client_profiles_client_display_name_min_length")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_client_profiles_created_by_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_client_profiles_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], name=op.f("fk_client_profiles_updated_by_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_profiles")),
        sa.UniqueConstraint("tenant_id", "client_code", name="uq_client_profiles_tenant_id_client_code"),
    )
    op.create_index(op.f("ix_client_profiles_created_by_user_id"), "client_profiles", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_client_profiles_status"), "client_profiles", ["status"], unique=False)
    op.create_index(op.f("ix_client_profiles_tenant_id"), "client_profiles", ["tenant_id"], unique=False)
    op.create_index("ix_client_profiles_tenant_status", "client_profiles", ["tenant_id", "status"], unique=False)
    op.create_index(op.f("ix_client_profiles_updated_by_user_id"), "client_profiles", ["updated_by_user_id"], unique=False)

    op.create_table(
        "client_consents",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.Enum("ANALYSIS", "HARMONIZATION", "TREND_ANALYSIS", "REPORT_EXPORT", "REPLAY_RESEARCH_USE", "HRV_PROCESSING", "MEDIA_UPLOAD_PROCESSING", name="consent_purpose"), nullable=False),
        sa.Column("status", sa.Enum("GRANTED", "REVOKED", name="consent_status"), nullable=False),
        sa.Column("consent_text_version", sa.String(length=80), nullable=False),
        sa.Column("recorded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["client_profiles.id"], name=op.f("fk_client_consents_client_id_client_profiles"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], name=op.f("fk_client_consents_recorded_by_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_client_consents_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_consents")),
    )
    op.create_index(op.f("ix_client_consents_client_id"), "client_consents", ["client_id"], unique=False)
    op.create_index(op.f("ix_client_consents_purpose"), "client_consents", ["purpose"], unique=False)
    op.create_index(op.f("ix_client_consents_recorded_by_user_id"), "client_consents", ["recorded_by_user_id"], unique=False)
    op.create_index(op.f("ix_client_consents_status"), "client_consents", ["status"], unique=False)
    op.create_index(op.f("ix_client_consents_tenant_id"), "client_consents", ["tenant_id"], unique=False)
    op.create_index("ix_client_consents_tenant_client", "client_consents", ["tenant_id", "client_id"], unique=False)
    op.create_index("ix_client_consents_tenant_purpose_status", "client_consents", ["tenant_id", "purpose", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_client_consents_tenant_purpose_status", table_name="client_consents")
    op.drop_index("ix_client_consents_tenant_client", table_name="client_consents")
    op.drop_index(op.f("ix_client_consents_tenant_id"), table_name="client_consents")
    op.drop_index(op.f("ix_client_consents_status"), table_name="client_consents")
    op.drop_index(op.f("ix_client_consents_recorded_by_user_id"), table_name="client_consents")
    op.drop_index(op.f("ix_client_consents_purpose"), table_name="client_consents")
    op.drop_index(op.f("ix_client_consents_client_id"), table_name="client_consents")
    op.drop_table("client_consents")
    op.drop_index(op.f("ix_client_profiles_updated_by_user_id"), table_name="client_profiles")
    op.drop_index("ix_client_profiles_tenant_status", table_name="client_profiles")
    op.drop_index(op.f("ix_client_profiles_tenant_id"), table_name="client_profiles")
    op.drop_index(op.f("ix_client_profiles_status"), table_name="client_profiles")
    op.drop_index(op.f("ix_client_profiles_created_by_user_id"), table_name="client_profiles")
    op.drop_table("client_profiles")
    op.execute("DROP TYPE IF EXISTS consent_status")
    op.execute("DROP TYPE IF EXISTS consent_purpose")
    op.execute("DROP TYPE IF EXISTS client_status")
