from fastapi.testclient import TestClient


def test_health_returns_status_ok():
    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "orchestrator" in data
    assert isinstance(data["orchestrator"], bool)
