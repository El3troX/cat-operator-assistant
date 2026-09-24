"""initial_schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-09-24 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("machine_id", sa.Text(), nullable=False),
        sa.Column("operator_id", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.create_index("ix_alerts_id", ["id"], unique=False)
        batch_op.create_index("ix_alerts_machine_id", ["machine_id"], unique=False)
        batch_op.create_index("ix_alerts_operator_id", ["operator_id"], unique=False)

    # incidents
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("machine_id", sa.Text(), nullable=False),
        sa.Column("operator_id", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.create_index("ix_incidents_id", ["id"], unique=False)
        batch_op.create_index("ix_incidents_machine_id", ["machine_id"], unique=False)
        batch_op.create_index("ix_incidents_operator_id", ["operator_id"], unique=False)

    # operation_log
    op.create_table(
        "operation_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.Text(), nullable=False),
        sa.Column("machine_id", sa.Text(), nullable=False),
        sa.Column("operator_id", sa.Text(), nullable=False),
        sa.Column("engine_hours", sa.Float(), nullable=True),
        sa.Column("fuel_used_l", sa.Float(), nullable=True),
        sa.Column("load_cycles", sa.Integer(), nullable=True),
        sa.Column("idling_time_min", sa.Integer(), nullable=True),
        sa.Column("seatbelt_status", sa.Text(), nullable=True),
        sa.Column("safety_alert_triggered", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("operation_log", schema=None) as batch_op:
        batch_op.create_index("ix_operation_log_id", ["id"], unique=False)
        batch_op.create_index("ix_operation_log_machine_id", ["machine_id"], unique=False)
        batch_op.create_index("ix_operation_log_operator_id", ["operator_id"], unique=False)

    # task_time_data
    op.create_table(
        "task_time_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Text(), nullable=True),
        sa.Column("task_type", sa.Text(), nullable=True),
        sa.Column("weather", sa.Text(), nullable=True),
        sa.Column("operator_skill", sa.Text(), nullable=True),
        sa.Column("machine_age_yrs", sa.Integer(), nullable=True),
        sa.Column("estimated_time_min", sa.Integer(), nullable=True),
        sa.Column("actual_time_min", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("task_time_data", schema=None) as batch_op:
        batch_op.create_index("ix_task_time_data_id", ["id"], unique=False)

    # tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("machine_id", sa.Text(), nullable=False),
        sa.Column("operator_id", sa.Text(), nullable=False),
        sa.Column("task_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="Pending", nullable=False),
        sa.Column("scheduled_time", sa.Text(), nullable=True),
        sa.Column("estimated_time_min", sa.Integer(), nullable=True),
        sa.Column("actual_time_min", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.create_index("ix_tasks_id", ["id"], unique=False)
        batch_op.create_index("ix_tasks_machine_id", ["machine_id"], unique=False)
        batch_op.create_index("ix_tasks_operator_id", ["operator_id"], unique=False)

    # training_modules
    op.create_table(
        "training_modules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("format", sa.Text(), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Integer(), server_default="0", nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("training_modules", schema=None) as batch_op:
        batch_op.create_index("ix_training_modules_id", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("training_modules")
    op.drop_table("tasks")
    op.drop_table("task_time_data")
    op.drop_table("operation_log")
    op.drop_table("incidents")
    op.drop_table("alerts")
