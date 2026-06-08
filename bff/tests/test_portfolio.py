from fastapi.testclient import TestClient


def test_get_portfolio_has_holdings():
    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    data = resp.json()
    assert "holdings" in data
    assert "total_value" in data
    assert data["total_value"] > 0
    symbols = {h["ticker"] for h in data["holdings"]}
    assert "NVDA" in symbols


def test_get_portfolio_holding_shape():
    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/portfolio")
    h = resp.json()["holdings"][0]
    for field in (
        "ticker",
        "name",
        "shares",
        "cost_basis",
        "current_price",
        "market_value",
        "pnl_pct",
    ):
        assert field in h


def test_get_portfolio_total_value_equals_sum_of_market_values():
    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/portfolio")
    data = resp.json()
    expected = round(sum(h["market_value"] for h in data["holdings"]), 2)
    assert abs(data["total_value"] - expected) < 0.01
