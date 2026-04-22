"""add priority and concurrent scheduling fields

Revision ID: 001_add_priority_concurrent
Revises: 
Create Date: 2026-02-27

新增字段：
- tasks.priority (VARCHAR2, default 'P2')
- tasks.priority_multiplier (DECIMAL(4,2), default 1.00)
- task_schedules.is_concurrent (BOOLEAN, default False)
- task_schedules.concurrent_with (INT, FK -> tasks.id)
- task_collaborators.scheduled_start (DATE)
- task_collaborators.scheduled_end (DATE)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '001_add_priority_concurrent'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tasks_columns = {col["name"] for col in inspector.get_columns("tasks")}
    task_schedules_columns = {col["name"] for col in inspector.get_columns("task_schedules")}
    task_collaborators_columns = {col["name"] for col in inspector.get_columns("task_collaborators")}
    tasks_indexes = {idx["name"] for idx in inspector.get_indexes("tasks")}

    # 1. tasks 表新增优先级字段
    if "priority" not in tasks_columns:
        op.add_column(
            'tasks',
            sa.Column('priority', sa.String(2), nullable=False, server_default='P2')
        )
    if "priority_multiplier" not in tasks_columns:
        op.add_column(
            'tasks',
            sa.Column('priority_multiplier', sa.Numeric(4, 2), nullable=False, server_default='1.00')
        )
    if "ix_tasks_priority" not in tasks_indexes:
        op.create_index('ix_tasks_priority', 'tasks', ['priority'])

    # 2. task_schedules 表新增并发排期字段
    if "is_concurrent" not in task_schedules_columns:
        op.add_column(
            'task_schedules',
            sa.Column('is_concurrent', sa.Boolean(), nullable=False, server_default=sa.false())
        )
    if "concurrent_with" not in task_schedules_columns:
        op.add_column(
            'task_schedules',
            sa.Column(
                'concurrent_with',
                sa.Integer(),
                sa.ForeignKey('tasks.id', ondelete='SET NULL'),
                nullable=True
            )
        )

    # 3. task_collaborators 表新增排期字段
    if "scheduled_start" not in task_collaborators_columns:
        op.add_column(
            'task_collaborators',
            sa.Column('scheduled_start', sa.Date(), nullable=True)
        )
    if "scheduled_end" not in task_collaborators_columns:
        op.add_column(
            'task_collaborators',
            sa.Column('scheduled_end', sa.Date(), nullable=True)
        )


def downgrade() -> None:
    # 回滚顺序与升级相反
    op.drop_column('task_collaborators', 'scheduled_end')
    op.drop_column('task_collaborators', 'scheduled_start')

    op.drop_column('task_schedules', 'concurrent_with')
    op.drop_column('task_schedules', 'is_concurrent')

    op.drop_index('ix_tasks_priority', table_name='tasks')
    op.drop_column('tasks', 'priority_multiplier')
    op.drop_column('tasks', 'priority')
