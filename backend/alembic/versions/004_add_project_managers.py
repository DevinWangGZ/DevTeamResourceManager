"""project_managers: 协办项目管理员

Revision ID: 004_add_project_managers
Revises: 003_add_login_protection_fields

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "004_add_project_managers"
down_revision = "003_add_login_protection_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "project_managers" not in tables:
        op.create_table(
            "project_managers",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("project_id", "user_id", name="uq_project_managers_proj_user"),
        )
        op.create_index("ix_project_managers_project_id", "project_managers", ["project_id"], unique=False)
        op.create_index("ix_project_managers_user_id", "project_managers", ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "project_managers" in inspector.get_table_names():
        op.drop_table("project_managers")
