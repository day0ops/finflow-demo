import httpx
import respx
from fastapi.testclient import TestClient


def _reset(client: TestClient):
    client.post(
        "/api/policies",
        json={
            "rbac": False,
            "elicitation": False,
            "rate_limit": False,
            "guardrails": False,
        },
    )


@respx.mock
def test_chat_briefing_proxies_to_orchestrator():
    respx.post("http://localhost:8000/run").mock(
        return_value=httpx.Response(
            200,
            json={
                "output": "Portfolio briefing: NVDA up 2.4%",
                "session_id": "s1",
                "agent": "finflow-orchestrator",
            },
        )
    )
    from main import app

    with TestClient(app) as client:
        _reset(client)
        resp = client.post("/api/chat", json={"message": "show my portfolio", "session_id": "s1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Portfolio briefing" in data["message"]
    assert data["trace"]["intent"] == "briefing"
    assert "portfolio-agent" in data["trace"]["agents"]
    assert data["elicitation"] is None


@respx.mock
def test_chat_rbac_blocks_trade_without_proxy():
    # No mock needed — RBAC should block before calling orchestrator
    from main import app

    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"rbac": True})
        resp = client.post("/api/chat", json={"message": "buy 10 shares of NVDA", "session_id": "s1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "denied" in data["message"].lower()
    assert data["trace"]["status_code"] == 403
    assert data["trace"]["policy_events"][0]["type"] == "rbac_block"
    assert data["trace"]["policy_events"][0]["verdict"] == "deny"
    assert data["elicitation"] is None


def test_chat_elicitation_gates_unconfirmed_trade():
    from main import app

    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"elicitation": True})
        resp = client.post("/api/chat", json={"message": "buy 10 shares of NVDA", "session_id": "s1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["elicitation"] is not None
    assert data["elicitation"]["required"] is True
    assert data["trace"]["policy_events"][0]["type"] == "elicitation_required"


@respx.mock
def test_chat_elicitation_confirmed_proxies():
    respx.post("http://localhost:8000/run").mock(
        return_value=httpx.Response(
            200,
            json={
                "output": "Trade executed: BUY 10 NVDA",
                "session_id": "s1",
                "agent": "finflow-orchestrator",
            },
        )
    )
    from main import app

    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"elicitation": True})
        resp = client.post(
            "/api/chat",
            json={
                "message": "buy 10 shares of NVDA",
                "session_id": "s1",
                "confirmed": True,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "Trade executed" in data["message"]
    assert data["elicitation"] is None


def test_chat_guardrail_blocks_advice_language():
    from main import app

    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"guardrails": True})
        resp = client.post(
            "/api/chat",
            json={
                "message": "give me a guaranteed profit trade",
                "session_id": "s1",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace"]["policy_events"][0]["type"] == "guardrail"
    assert data["trace"]["policy_events"][0]["verdict"] == "deny"
    assert data["trace"]["status_code"] == 400


def test_chat_rate_limit_adds_allow_event():
    from main import app

    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"rate_limit": True, "elicitation": True})
        resp = client.post("/api/chat", json={"message": "buy 5 AAPL", "session_id": "s1"})
    data = resp.json()
    types = [e["type"] for e in data["trace"]["policy_events"]]
    assert "rate_limit" in types
    rate_evt = next(e for e in data["trace"]["policy_events"] if e["type"] == "rate_limit")
    assert rate_evt["verdict"] == "allow"
