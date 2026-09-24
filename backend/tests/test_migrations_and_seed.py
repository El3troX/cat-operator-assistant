from pathlib import Path

from alembic import command
from migrations import apply_migrations, get_alembic_config
from models import TrainingModule
from seed import seed_reference_data, seed_sample_data
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker


def test_alembic_upgrade_and_downgrade(tmp_path: Path):
    db_file = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    cfg = get_alembic_config(database_url=db_url)

    # 1. Upgrade to head
    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    insp = inspect(engine)
    tables = insp.get_table_names()

    expected_tables = {
        "alembic_version",
        "alerts",
        "incidents",
        "operation_log",
        "task_time_data",
        "tasks",
        "training_modules",
    }
    assert expected_tables.issubset(set(tables))

    # Verify high-frequency query indexes
    op_indexes = {idx["name"] for idx in insp.get_indexes("operation_log")}
    assert "ix_operation_log_timestamp" in op_indexes
    assert "ix_operation_log_machine_ts" in op_indexes
    assert "ix_operation_log_operator_ts" in op_indexes

    task_indexes = {idx["name"] for idx in insp.get_indexes("tasks")}
    assert "ix_tasks_status" in task_indexes
    assert "ix_tasks_scheduled_time" in task_indexes

    alert_indexes = {idx["name"] for idx in insp.get_indexes("alerts")}
    assert "ix_alerts_timestamp" in alert_indexes
    assert "ix_alerts_machine_ts" in alert_indexes
    assert "ix_alerts_operator_ts" in alert_indexes

    # 2. Downgrade to base
    command.downgrade(cfg, "base")
    insp_after = inspect(engine)
    remaining_tables = set(insp_after.get_table_names())
    assert "operation_log" not in remaining_tables
    assert "tasks" not in remaining_tables
    assert "alerts" not in remaining_tables


def test_apply_migrations_helper(tmp_path: Path):
    db_file = tmp_path / "test_apply_helper.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    apply_migrations(database_url=db_url)

    engine = create_engine(db_url)
    insp = inspect(engine)
    assert "training_modules" in insp.get_table_names()


def test_seed_reference_data_is_idempotent(tmp_path: Path):
    db_file = tmp_path / "test_seed_ref.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    apply_migrations(database_url=db_url)
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        added_1 = seed_reference_data(db)
        assert added_1 == 4
        assert db.query(TrainingModule).count() == 4

        # Second run should be a no-op
        added_2 = seed_reference_data(db)
        assert added_2 == 0
        assert db.query(TrainingModule).count() == 4


def test_seed_sample_data_preserves_reference_catalog(tmp_path: Path):
    db_file = tmp_path / "test_seed_sample.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    apply_migrations(database_url=db_url)
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        seed_reference_data(db)

        # Mark a module as completed by an operator
        module = db.query(TrainingModule).filter(TrainingModule.title == "Safe Excavation Basics").first()
        assert module is not None
        module.completed = 1
        db.commit()

        # Seed sample data with reset=True
        counts = seed_sample_data(db, reset=True)
        assert counts["tasks"] == 14
        assert counts["operation_log"] > 0

        # Reference module should still exist and preserve completed=1
        reloaded_module = db.query(TrainingModule).filter(TrainingModule.title == "Safe Excavation Basics").first()
        assert reloaded_module is not None
        assert reloaded_module.completed == 1
        assert db.query(TrainingModule).count() == 4
