"""identity tenant audit baseline

Revision ID: 0001_identity_tenant_audit
Revises: None
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_identity_tenant_audit"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "SUSPENDED", "ARCHIVED", name="tenant_status"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(slug) >= 3", name=op.f("ck_tenants_tenant_slug_min_length")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tenants")),
    )
    op.create_index(op.f("ix_tenants_slug"), "tenants", ["slug"], unique=True)

    op.create_table(
        "roles",
        sa.Column("name", sa.Enum("ADMIN", "THERAPIST", "ASSISTANT", "CLIENT", "RESEARCHER", "SYSTEM", name="role_name"), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("name", name=op.f("uq_roles_name")),
    )

    op.create_table(
        "users",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "INVITED", "DISABLED", name="user_status"), nullable=False),
        sa.Column("is_mfa_enabled", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_users_role_id_roles"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_users_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_id_email"),
    )
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)
    op.create_index("ix_users_tenant_role", "users", ["tenant_id", "role_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.Enum("LOGIN_SECURITY_EVENT", "CLIENT_CREATE_UPDATE_DELETE", "CONSENT_CHANGE", "SESSION_START", "ENGINE_RUN", "HARMONIZATION_APPROVAL_JOB", "REPORT_EXPORT", "GDPR_EXPORT_DELETE_ANONYMIZE", "ADMIN_CONFIG_CHANGE", name="audit_action"), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.String(length=120), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_logs_actor_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_audit_logs_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_correlation_id"), "audit_logs", ["correlation_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_tenant_id"), "audit_logs", ["tenant_id"], unique=False)
    op.create_index("ix_audit_logs_tenant_action_created", "audit_logs", ["tenant_id", "action", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_tenant_action_created", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_tenant_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_correlation_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_users_tenant_role", table_name="users")
    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_index(op.f("ix_tenants_slug"), table_name="tenants")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS audit_action")
    op.execute("DROP TYPE IF EXISTS user_status")
    op.execute("DROP TYPE IF EXISTS role_name")
    op.execute("DROP TYPE IF EXISTS tenant_status")
