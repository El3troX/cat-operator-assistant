import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import inspect
from database import Base, SessionLocal, engine
import models
from main import app, get_safety_alerts, get_tasks_today, health_check, root


def test_database_tables():
    print("Testing database table creation...")
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = {
        "operation_log": [
            "id", "timestamp", "machine_id", "operator_id",
            "engine_hours", "fuel_used_l", "load_cycles",
            "idling_time_min", "seatbelt_status", "safety_alert_triggered"
        ],
        "task_time_data": [
            "id", "task_id", "task_type", "weather",
            "operator_skill", "machine_age_yrs", "estimated_time_min",
            "actual_time_min"
        ],
        "tasks": [
            "id", "machine_id", "operator_id", "task_type",
            "status", "scheduled_time", "estimated_time_min",
            "actual_time_min"
        ],
        "incidents": [
            "id", "machine_id", "operator_id", "description",
            "severity", "timestamp"
        ],
        "alerts": [
            "id", "machine_id", "operator_id", "type",
            "severity", "message", "timestamp"
        ],
        "training_modules": [
            "id", "title", "format", "duration_min", "completed"
        ]
    }

    for table_name, expected_cols in expected_tables.items():
        assert table_name in tables, f"Missing table: {table_name}"
        cols = [col["name"] for col in inspector.get_columns(table_name)]
        for col in expected_cols:
            assert col in cols, f"Missing column '{col}' in table '{table_name}'"

    print("All 6 tables and columns verified successfully against CONTRACT.md!")


def test_direct_route_handlers():
    print("\nTesting route handlers directly...")
    db = SessionLocal()
    try:
        tasks = get_tasks_today(db)
        print(f"get_tasks_today() returned {len(tasks)} tasks.")
        assert len(tasks) > 0, "Expected at least 1 task"
        first_task = tasks[0]
        assert hasattr(first_task, "machine_id")
        assert hasattr(first_task, "operator_id")
        assert hasattr(first_task, "task_type")
        assert hasattr(first_task, "status")
        assert hasattr(first_task, "scheduled_time")
        assert hasattr(first_task, "estimated_time_min")
        assert hasattr(first_task, "actual_time_min")

        alerts_all = get_safety_alerts(None, db)
        print(f"get_safety_alerts(None) returned {len(alerts_all)} alerts.")
        assert len(alerts_all) > 0, "Expected at least 1 alert"

        alerts_exc001 = get_safety_alerts("EXC001", db)
        print(f"get_safety_alerts('EXC001') returned {len(alerts_exc001)} alerts.")
        for a in alerts_exc001:
            assert a.machine_id == "EXC001"
    finally:
        db.close()


async def request_asgi(path: str, query_string: str = ""):
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": query_string.encode("utf-8"),
        "headers": [],
        "server": ("127.0.0.1", 8000),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    }

    status_code = None
    response_body = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]
        elif message["type"] == "http.response.body":
            response_body.append(message.get("body", b""))

    await app(scope, receive, send)
    body = b"".join(response_body).decode("utf-8")
    return status_code, json.loads(body)


async def test_asgi_endpoints():
    print("\nTesting ASGI interface directly...")

    # /health
    status, body = await request_asgi("/health")
    assert status == 200
    assert body["status"] == "ok"
    print("ASGI GET /health passed:", body)

    # /tasks/today
    status, body = await request_asgi("/tasks/today")
    assert status == 200
    assert isinstance(body, list)
    assert len(body) > 0
    sample_task = body[0]
    expected_task_fields = {
        "id", "machine_id", "operator_id", "task_type",
        "status", "scheduled_time", "estimated_time_min", "actual_time_min"
    }
    assert expected_task_fields.issubset(sample_task.keys()), f"Task keys mismatch: {sample_task.keys()}"
    print(f"ASGI GET /tasks/today passed with {len(body)} tasks. Sample:", sample_task)

    # /safety/alerts
    status, body = await request_asgi("/safety/alerts")
    assert status == 200
    assert isinstance(body, list)
    assert len(body) > 0
    sample_alert = body[0]
    expected_alert_fields = {
        "id", "machine_id", "operator_id", "type",
        "severity", "message", "timestamp"
    }
    assert expected_alert_fields.issubset(sample_alert.keys()), f"Alert keys mismatch: {sample_alert.keys()}"
    print(f"ASGI GET /safety/alerts passed with {len(body)} alerts. Sample:", sample_alert)

    # /safety/alerts?machine_id=EXC001
    status, body = await request_asgi("/safety/alerts", query_string="machine_id=EXC001")
    assert status == 200
    assert isinstance(body, list)
    for a in body:
        assert a["machine_id"] == "EXC001"
    print(f"ASGI GET /safety/alerts?machine_id=EXC001 passed with {len(body)} alerts.")


if __name__ == "__main__":
    test_database_tables()
    test_direct_route_handlers()
    asyncio.run(test_asgi_endpoints())
    print("\nAll verification tests passed cleanly!")
