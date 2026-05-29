"""add user password hash

Revision ID: 0002_user_password_hash
Revises: 0001_identity_tenant_audit
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_user_password_hash"
down_revision = "0001_identity_tenant_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=300), nullable=False, server_default="UNUSABLE"),
    )
    op.alter_column("users", "password_hash", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "password_hash")
