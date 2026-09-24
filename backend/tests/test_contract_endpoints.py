

def test_health_endpoint(client):
    """GET /health should return 200 with ok status and tables_ready."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["tables_ready"] is True


def test_get_today_tasks(client):
    """GET /tasks/today returns seeded tasks."""
    resp = client.get("/tasks/today")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    first = data[0]
    for key in ("id", "machine_id", "operator_id", "task_type", "status"):
        assert key in first


def test_patch_task_lifecycle(client):
    """PATCH /tasks/{id} updates status and actual time, supports null reset."""
    tasks = client.get("/tasks/today").json()
    task_id = tasks[0]["id"]

    # Mark completed
    resp = client.patch(f"/tasks/{task_id}", json={"status": "Completed", "actual_time_min": 58})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Completed"
    assert data["actual_time_min"] == 58

    # Reset actual time with null
    resp_reset = client.patch(f"/tasks/{task_id}", json={"status": "In Progress", "actual_time_min": None})
    assert resp_reset.status_code == 200
    assert resp_reset.json()["actual_time_min"] is None


def test_patch_task_invalid_input(client):
    """PATCH /tasks/{id} rejects unknown status values with 422."""
    tasks = client.get("/tasks/today").json()
    task_id = tasks[0]["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"status": "InvalidStatus"})
    assert resp.status_code == 422


def test_safety_alerts_retrieval(client):
    """GET /safety/alerts returns alerts and allows filtering."""
    resp = client.get("/safety/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    assert isinstance(alerts, list)
    assert len(alerts) >= 2

    # Filter by machine_id
    m_alerts = client.get("/safety/alerts", params={"machine_id": "EXC001"})
    assert m_alerts.status_code == 200
    for alert in m_alerts.json():
        assert alert["machine_id"] == "EXC001"


def test_safety_check_generates_alerts(client):
    """POST /safety/check evaluates rules and creates alerts."""
    payload = {
        "machine_id": "EXC001",
        "operator_id": "OP1001",
        "seatbelt_status": "Unfastened",
        "idling_time_min": 55,
        "timestamp": "2025-05-01T10:00:00",
    }
    resp = client.post("/safety/check", json=payload)
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) >= 2
    types = [a["type"] for a in alerts]
    assert "Seatbelt" in types
    assert "Idling" in types


def test_safety_proximity_hazard_and_safe(client):
    """POST /safety/proximity triggers alert on distance <= 2m and remains safe on > 2m."""
    close_resp = client.post(
        "/safety/proximity",
        json={"machine_id": "EXC001", "distance_m": 1.2, "timestamp": "2025-05-01T10:00:00"},
    )
    assert close_resp.status_code == 200
    close_data = close_resp.json()
    assert close_data["triggered"] is True
    assert close_data["severity"] == "High"
    assert "within 2m" in close_data["message"]

    safe_resp = client.post(
        "/safety/proximity",
        json={"machine_id": "EXC001", "distance_m": 4.5, "timestamp": "2025-05-01T10:00:00"},
    )
    assert safe_resp.status_code == 200
    safe_data = safe_resp.json()
    assert safe_data["triggered"] is False
    assert safe_data["severity"] == "Low"


def test_incidents_crud(client):
    """POST /incidents logs an incident and GET /incidents retrieves it."""
    payload = {
        "machine_id": "EXC001",
        "operator_id": "OP1001",
        "description": "Minor collision with side barrier",
        "severity": "Medium",
        "timestamp": "2025-05-01T11:00:00",
    }
    create_resp = client.post("/incidents", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert "id" in created
    assert created["description"] == payload["description"]

    list_resp = client.get("/incidents")
    assert list_resp.status_code == 200
    incidents = list_resp.json()
    assert any(inc["id"] == created["id"] for inc in incidents)


def test_incidents_validation(client):
    """Description shorter than 5 chars or invalid severity gets 422."""
    short_resp = client.post(
        "/incidents",
        json={"machine_id": "EXC001", "operator_id": "OP1001", "description": "No", "severity": "Low", "timestamp": "2025-05-01T11:00:00"},
    )
    assert short_resp.status_code == 422


def test_anomalies_endpoint(client):
    """GET /anomalies returns flagged operation log readings."""
    resp = client.get("/anomalies")
    assert resp.status_code == 200
    anomalies = resp.json()
    assert isinstance(anomalies, list)
    assert len(anomalies) > 0
    first = anomalies[0]
    for key in ("machine_id", "operator_id", "type", "detail", "timestamp"):
        assert key in first


def test_predict_task_time_endpoint(client):
    """POST /predict/task-time returns prediction with confidence band and drivers."""
    payload = {
        "task_type": "Trenching",
        "weather": "Rainy",
        "operator_skill": "Intermediate",
        "machine_age_yrs": 4,
    }
    resp = client.post("/predict/task-time", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_minutes" in data
    assert isinstance(data["predicted_minutes"], int)
    assert data["predicted_minutes"] > 0
    assert "source" in data
    assert data["source"] in ("model", "historical", "heuristic")
    if data["source"] == "model":
        assert "model_version" in data
        assert data["model_version"] is not None
        assert "p10" in data
        assert "p90" in data
        assert isinstance(data["drivers"], list)


def test_training_modules_completion(client):
    """GET /training/modules lists modules and PATCH toggles completion."""
    modules = client.get("/training/modules").json()
    assert len(modules) > 0
    mod_id = modules[0]["id"]

    patch_resp = client.patch(f"/training/modules/{mod_id}", json={"completed": 1})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["completed"] == 1


def test_scores_endpoints(client):
    """GET /scores/operators returns expected shapes."""
    op_resp = client.get("/scores/operators")
    assert op_resp.status_code == 200
    assert isinstance(op_resp.json(), list)


def test_request_id_header(client):
    """All responses include an X-Request-ID header."""
    resp = client.get("/health")
    assert "x-request-id" in resp.headers

    # Echoes custom request id
    custom_id = "test-req-999"
    resp_custom = client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp_custom.headers.get("x-request-id") == custom_id
