"""add task_comments table

Revision ID: 002_add_task_comments
Revises: 001_add_priority_concurrent
Create Date: 2026-02-27

新增：
- task_comments 表：存储任务参与者（发布人/认领人/协助人）的留言/备注
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_task_comments'
down_revision = '001_add_priority_concurrent'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'task_comments',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_comments_id', 'task_comments', ['id'])
    op.create_index('ix_task_comments_task_id', 'task_comments', ['task_id'])
    op.create_index('ix_task_comments_user_id', 'task_comments', ['user_id'])
    op.create_index('ix_task_comments_created_at', 'task_comments', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_task_comments_created_at', table_name='task_comments')
    op.drop_index('ix_task_comments_user_id', table_name='task_comments')
    op.drop_index('ix_task_comments_task_id', table_name='task_comments')
    op.drop_index('ix_task_comments_id', table_name='task_comments')
    op.drop_table('task_comments')
