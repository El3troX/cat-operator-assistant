import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from database import engine
from main import app
from migrations import apply_migrations
from sqlalchemy import inspect


def test_database_tables():
    print("Testing database table creation & migrations...")
    apply_migrations()

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


async def request_asgi(method: str, path: str, query_string: str = "", json_data: dict = None):
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": query_string.encode("utf-8"),
        "headers": [(b"content-type", b"application/json")] if json_data else [],
        "server": ("127.0.0.1", 8000),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    }

    req_body = json.dumps(json_data).encode("utf-8") if json_data else b""
    sent_body = False

    async def receive():
        nonlocal sent_body
        if not sent_body:
            sent_body = True
            return {"type": "http.request", "body": req_body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    status_code = None
    response_body = []

    async def send(message):
        nonlocal status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]
        elif message["type"] == "http.response.body":
            response_body.append(message.get("body", b""))

    await app(scope, receive, send)
    body_str = b"".join(response_body).decode("utf-8")
    body_json = json.loads(body_str) if body_str else None
    return status_code, body_json


async def test_all_contract_endpoints():
    print("\n" + "=" * 60)
    print("Testing All CONTRACT.md Endpoints via ASGI...")
    print("=" * 60)

    # 1. Health check
    status, body = await request_asgi("GET", "/health")
    assert status == 200
    assert body["status"] == "ok"
    assert body["tables_ready"] is True
    print("[PASS] GET /health ->", body)

    # 2. GET /tasks/today
    status, body = await request_asgi("GET", "/tasks/today")
    assert status == 200
    assert isinstance(body, list)
    assert len(body) > 0
    task_id = body[0]["id"]
    print(f"[PASS] GET /tasks/today -> {len(body)} tasks, sample id={task_id}")

    # 3. PATCH /tasks/{id}
    patch_payload = {"status": "Completed", "actual_time_min": 58}
    status, body = await request_asgi("PATCH", f"/tasks/{task_id}", json_data=patch_payload)
    assert status == 200
    assert body["status"] == "Completed"
    assert body["actual_time_min"] == 58
    print(f"[PASS] PATCH /tasks/{task_id} -> status={body['status']}, actual_time_min={body['actual_time_min']}")

    # 4. GET /safety/alerts
    status, body = await request_asgi("GET", "/safety/alerts")
    assert status == 200
    assert isinstance(body, list)
    print(f"[PASS] GET /safety/alerts -> {len(body)} alerts")

    # 5. GET /safety/alerts?machine_id=EXC001
    status, body = await request_asgi("GET", "/safety/alerts", query_string="machine_id=EXC001")
    assert status == 200
    for a in body:
        assert a["machine_id"] == "EXC001"
    print(f"[PASS] GET /safety/alerts?machine_id=EXC001 -> {len(body)} alerts")

    # 6. POST /safety/check
    check_payload = {
        "machine_id": "EXC001",
        "operator_id": "OP1001",
        "seatbelt_status": "Unfastened",
        "idling_time_min": 55,
        "timestamp": "2025-05-01T10:00:00"
    }
    status, body = await request_asgi("POST", "/safety/check", json_data=check_payload)
    assert status == 200
    assert isinstance(body, list)
    assert len(body) >= 2  # Seatbelt + Idling
    alert_types = [a["type"] for a in body]
    assert "Seatbelt" in alert_types
    assert "Idling" in alert_types
    print(f"[PASS] POST /safety/check -> generated {len(body)} alerts: {alert_types}")

    # 7. POST /safety/proximity (Triggered)
    prox_payload_close = {"machine_id": "EXC001", "distance_m": 1.2, "timestamp": "2025-05-01T10:00:00"}
    status, body = await request_asgi("POST", "/safety/proximity", json_data=prox_payload_close)
    assert status == 200
    assert body["triggered"] is True
    assert body["severity"] == "High"
    assert "within 2m" in body["message"]
    print(f"[PASS] POST /safety/proximity (1.2m) -> triggered={body['triggered']}, severity={body['severity']}")

    # 8. POST /safety/proximity (Safe)
    prox_payload_safe = {"machine_id": "EXC001", "distance_m": 4.5, "timestamp": "2025-05-01T10:00:00"}
    status, body = await request_asgi("POST", "/safety/proximity", json_data=prox_payload_safe)
    assert status == 200
    assert body["triggered"] is False
    assert body["severity"] == "Low"
    print(f"[PASS] POST /safety/proximity (4.5m) -> triggered={body['triggered']}, severity={body['severity']}")

    # 9. POST /incidents
    inc_payload = {
        "machine_id": "EXC001",
        "operator_id": "OP1001",
        "description": "Minor collision with barrier",
        "severity": "Medium",
        "timestamp": "2025-05-01T11:00:00"
    }
    status, body = await request_asgi("POST", "/incidents", json_data=inc_payload)
    assert status == 201
    assert "id" in body
    assert body["machine_id"] == "EXC001"
    print(f"[PASS] POST /incidents -> created incident id={body['id']}")

    # 10. GET /incidents
    status, body = await request_asgi("GET", "/incidents")
    assert status == 200
    assert isinstance(body, list)
    assert len(body) > 0
    print(f"[PASS] GET /incidents -> {len(body)} incidents")

    # 11. GET /anomalies
    status, body = await request_asgi("GET", "/anomalies")
    assert status == 200
    assert isinstance(body, list)
    assert len(body) > 0
    sample_anomaly = body[0]
    expected_anomaly_fields = {"machine_id", "operator_id", "type", "detail", "timestamp"}
    assert expected_anomaly_fields.issubset(sample_anomaly.keys())
    print(f"[PASS] GET /anomalies -> {len(body)} anomalies, sample: {sample_anomaly}")

    # 12. POST /predict/task-time
    pred_payload = {
        "task_type": "Trenching",
        "weather": "Rainy",
        "operator_skill": "Intermediate",
        "machine_age_yrs": 4
    }
    status, body = await request_asgi("POST", "/predict/task-time", json_data=pred_payload)
    assert status == 200
    assert "predicted_minutes" in body
    assert isinstance(body["predicted_minutes"], int)
    assert body["predicted_minutes"] > 0
    print(f"[PASS] POST /predict/task-time -> predicted_minutes={body['predicted_minutes']}")

    # 13. GET /training/modules
    status, body = await request_asgi("GET", "/training/modules")
    assert status == 200
    assert isinstance(body, list)
    assert len(body) > 0
    module_id = body[0]["id"]
    print(f"[PASS] GET /training/modules -> {len(body)} modules, sample id={module_id}")

    # 14. PATCH /training/modules/{id}
    patch_mod_payload = {"completed": 1}
    status, body = await request_asgi("PATCH", f"/training/modules/{module_id}", json_data=patch_mod_payload)
    assert status == 200
    assert body["completed"] == 1
    print(f"[PASS] PATCH /training/modules/{module_id} -> completed={body['completed']}")

    print("=" * 60)
    print("ALL 14 ENDPOINT TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    test_database_tables()
    asyncio.run(test_all_contract_endpoints())
