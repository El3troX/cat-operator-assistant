from services.copilot_offline import _severity


def test_copilot_severity_parser():
    """Verify keyword severity parser for offline copilot."""
    assert _severity("I clipped the fence, nobody hurt") == "Medium"
    assert _severity("Worker fell and was hurt badly") == "High"
    assert _severity("Just finishing up routine inspection") == "Low"


def test_copilot_chat_offline_mode(client):
    """When ANTHROPIC_API_KEY is unset, copilot falls back to offline keyword parser."""
    payload = {
        "operator_id": "OP1001",
        "machine_id": "EXC001",
        "messages": [{"role": "user", "content": "What is my next task?"}],
    }
    resp = client.post("/copilot/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "offline"
    assert "reply" in data
    assert len(data["reply"]) > 0


def test_copilot_chat_draft_incident(client):
    """Incident report speech generates a drafted incident awaiting confirmation."""
    payload = {
        "operator_id": "OP1001",
        "machine_id": "EXC001",
        "messages": [{"role": "user", "content": "Log incident: hit a rock, hydraulic line dented"}],
    }
    resp = client.post("/copilot/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "offline"
    assert data["draft_incident"] is not None
    assert data["draft_incident"]["severity"] in ("Low", "Medium", "High")
    assert "hydraulic" in data["draft_incident"]["description"].lower()
