from fastapi.testclient import TestClient


def test_get_tickers_returns_all_symbols():
    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/tickers")
    assert resp.status_code == 200
    data = resp.json()
    assert "tickers" in data
    symbols = {t["ticker"] for t in data["tickers"]}
    assert symbols >= {"NVDA", "AAPL", "MSFT", "GOOGL", "AMZN"}


def test_get_tickers_shape():
    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/tickers")
    first = resp.json()["tickers"][0]
    assert "ticker" in first
    assert "name" in first
    assert "price" in first
    assert "change_pct" in first
    assert "volume" in first
