"""add login protection fields for users

Revision ID: 003_add_login_protection_fields
Revises: 002_add_task_comments
Create Date: 2026-04-22

新增字段：
- users.failed_login_attempts
- users.last_failed_login_at
- users.locked_until
- users.last_login_at
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "003_add_login_protection_fields"
down_revision = "002_add_task_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    user_indexes = {idx["name"] for idx in inspector.get_indexes("users")}

    if "failed_login_attempts" not in user_columns:
        op.add_column(
            "users",
            sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        )
    if "last_failed_login_at" not in user_columns:
        op.add_column(
            "users",
            sa.Column("last_failed_login_at", sa.TIMESTAMP(), nullable=True),
        )
    if "locked_until" not in user_columns:
        op.add_column(
            "users",
            sa.Column("locked_until", sa.TIMESTAMP(), nullable=True),
        )
    if "last_login_at" not in user_columns:
        op.add_column(
            "users",
            sa.Column("last_login_at", sa.TIMESTAMP(), nullable=True),
        )
    if "ix_users_locked_until" not in user_indexes:
        op.create_index("ix_users_locked_until", "users", ["locked_until"])


def downgrade() -> None:
    op.drop_index("ix_users_locked_until", table_name="users")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "last_failed_login_at")
    op.drop_column("users", "failed_login_attempts")
