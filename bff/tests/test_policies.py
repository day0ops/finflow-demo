from fastapi.testclient import TestClient


def _reset(client: TestClient):
    client.post(
        "/api/policies",
        json={"rbac": False, "elicitation": False, "rate_limit": False, "guardrails": False},
    )


def test_get_policies_default_all_false():
    from main import app

    with TestClient(app) as client:
        _reset(client)
        resp = client.get("/api/policies")
    assert resp.status_code == 200
    assert resp.json() == {
        "rbac": False,
        "elicitation": False,
        "rate_limit": False,
        "guardrails": False,
    }


def test_post_policies_enables_rbac():
    from main import app

    with TestClient(app) as client:
        _reset(client)
        resp = client.post("/api/policies", json={"rbac": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["rbac"] is True
    assert data["elicitation"] is False


def test_post_policies_partial_update_preserves_other_fields():
    from main import app

    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"elicitation": True})
        resp = client.post("/api/policies", json={"rbac": True})
    data = resp.json()
    assert data["rbac"] is True
    assert data["elicitation"] is True
    assert data["rate_limit"] is False
