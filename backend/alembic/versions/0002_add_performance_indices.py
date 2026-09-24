"""add_performance_indices

Revision ID: 0002_add_performance_indices
Revises: 0001_initial_schema
Create Date: 2026-09-24 11:10:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_performance_indices"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alerts indices
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.create_index("ix_alerts_timestamp", ["timestamp"], unique=False)
        batch_op.create_index("ix_alerts_machine_ts", ["machine_id", "timestamp"], unique=False)
        batch_op.create_index("ix_alerts_operator_ts", ["operator_id", "timestamp"], unique=False)

    # 2. Incidents indices
    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.create_index("ix_incidents_timestamp", ["timestamp"], unique=False)
        batch_op.create_index("ix_incidents_machine_ts", ["machine_id", "timestamp"], unique=False)
        batch_op.create_index("ix_incidents_operator_ts", ["operator_id", "timestamp"], unique=False)

    # 3. OperationLog indices
    with op.batch_alter_table("operation_log", schema=None) as batch_op:
        batch_op.create_index("ix_operation_log_timestamp", ["timestamp"], unique=False)
        batch_op.create_index("ix_operation_log_machine_ts", ["machine_id", "timestamp"], unique=False)
        batch_op.create_index("ix_operation_log_operator_ts", ["operator_id", "timestamp"], unique=False)

    # 4. Tasks indices
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.create_index("ix_tasks_status", ["status"], unique=False)
        batch_op.create_index("ix_tasks_scheduled_time", ["scheduled_time"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_index("ix_tasks_scheduled_time")
        batch_op.drop_index("ix_tasks_status")

    with op.batch_alter_table("operation_log", schema=None) as batch_op:
        batch_op.drop_index("ix_operation_log_operator_ts")
        batch_op.drop_index("ix_operation_log_machine_ts")
        batch_op.drop_index("ix_operation_log_timestamp")

    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.drop_index("ix_incidents_operator_ts")
        batch_op.drop_index("ix_incidents_machine_ts")
        batch_op.drop_index("ix_incidents_timestamp")

    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.drop_index("ix_alerts_operator_ts")
        batch_op.drop_index("ix_alerts_machine_ts")
        batch_op.drop_index("ix_alerts_timestamp")
