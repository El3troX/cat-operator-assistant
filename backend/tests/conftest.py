import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure root repo is in sys.path for ml package
REPO_ROOT = BACKEND_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set test environment flags before importing app/config
os.environ["SIM_ENABLED"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"

import models
from database import Base, get_db
from main import app
from services.scoring import ensure_training_catalog


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("db")
    return temp_dir / "test_assistant.db"


@pytest.fixture(scope="session")
def db_engine(test_db_path):
    url = f"sqlite:///{test_db_path.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def session_factory(db_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture(scope="function")
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def seed_test_data(db_session):
    """Seed test database with predictable fixture data for tests."""
    db_session.query(models.OperationLog).delete()
    db_session.query(models.TaskTimeData).delete()
    db_session.query(models.Task).delete()
    db_session.query(models.Incident).delete()
    db_session.query(models.Alert).delete()
    db_session.query(models.TrainingModule).delete()
    db_session.commit()

    # Seed modules
    ensure_training_catalog(db_session)
    extra_modules = [
        models.TrainingModule(title="Reducing Idle Time & Fuel Conservation", format="Simulation", duration_min=15, completed=0),
        models.TrainingModule(title="Proximity Awareness & Site Safety", format="Video", duration_min=10, completed=0),
        models.TrainingModule(title="Safe Excavation Basics", format="Instructor", duration_min=20, completed=0),
    ]
    db_session.add_all(extra_modules)

    # Seed tasks
    tasks = [
        models.Task(
            machine_id="EXC001",
            operator_id="OP1001",
            task_type="Trenching",
            status="Pending",
            scheduled_time="2025-05-01T08:00:00",
            estimated_time_min=50,
            actual_time_min=None,
        ),
        models.Task(
            machine_id="EXC001",
            operator_id="OP1001",
            task_type="Material Loading",
            status="In Progress",
            scheduled_time="2025-05-01T10:00:00",
            estimated_time_min=30,
            actual_time_min=None,
        ),
        models.Task(
            machine_id="EXC002",
            operator_id="OP1002",
            task_type="Earth Excavation",
            status="Completed",
            scheduled_time="2025-05-01T13:00:00",
            estimated_time_min=60,
            actual_time_min=58,
        ),
    ]
    db_session.add_all(tasks)

    # Seed operation logs
    logs = [
        models.OperationLog(
            timestamp="2025-05-01T08:00:00",
            machine_id="EXC001",
            operator_id="OP1001",
            engine_hours=120.5,
            fuel_used_l=15.2,
            load_cycles=10,
            idling_time_min=55,
            seatbelt_status="Unfastened",
            safety_alert_triggered=1,
        ),
        models.OperationLog(
            timestamp="2025-05-01T09:00:00",
            machine_id="EXC001",
            operator_id="OP1001",
            engine_hours=121.5,
            fuel_used_l=12.0,
            load_cycles=8,
            idling_time_min=20,
            seatbelt_status="Fastened",
            safety_alert_triggered=0,
        ),
        models.OperationLog(
            timestamp="2025-05-01T08:30:00",
            machine_id="EXC002",
            operator_id="OP1002",
            engine_hours=85.0,
            fuel_used_l=18.0,
            load_cycles=12,
            idling_time_min=10,
            seatbelt_status="Fastened",
            safety_alert_triggered=0,
        ),
    ]
    db_session.add_all(logs)

    # Seed alerts
    alerts = [
        models.Alert(
            machine_id="EXC001",
            operator_id="OP1001",
            type="Seatbelt",
            severity="High",
            message="Seatbelt unfastened during operation",
            timestamp="2025-05-01T08:00:00",
        ),
        models.Alert(
            machine_id="EXC002",
            operator_id="OP1002",
            type="Idling",
            severity="Medium",
            message="Idling time 55min exceeds threshold (45min)",
            timestamp="2025-05-01T08:30:00",
        ),
    ]
    db_session.add_all(alerts)

    # Seed incidents
    incidents = [
        models.Incident(
            machine_id="EXC001",
            operator_id="OP1001",
            description="Minor scrape on bucket edge",
            severity="Low",
            timestamp="2025-05-01T07:45:00",
        )
    ]
    db_session.add_all(incidents)

    db_session.commit()
    return db_session


@pytest.fixture(scope="function")
def client(session_factory, seed_test_data):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()
