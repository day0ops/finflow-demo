import json

import db as db_module
import pytest
from fastmcp import Client
from server import mcp


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    """Replace the module-level connection with a seeded in-memory DB."""
    conn = db_module.get_connection(":memory:")
    db_module.seed_db(conn)

    import server

    monkeypatch.setattr(server, "_conn", conn)
    monkeypatch.setattr(server, "_DB_PATH", ":memory:")
    yield conn
    conn.close()
    monkeypatch.setattr(server, "_conn", None)


@pytest.mark.asyncio
async def test_get_portfolio_morgan():
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio", {"user_id": "morgan"})
    data = json.loads(result.content[0].text)
    assert data["user_id"] == "morgan"
    assert len(data["positions"]) == 4
    tickers = [p["ticker"] for p in data["positions"]]
    assert "NVDA" in tickers
    assert "MSFT" in tickers
    assert data["total_pl"] != 0


@pytest.mark.asyncio
async def test_get_portfolio_alex():
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio", {"user_id": "alex"})
    data = json.loads(result.content[0].text)
    assert data["user_id"] == "alex"
    assert len(data["positions"]) == 2
    tickers = [p["ticker"] for p in data["positions"]]
    assert "AAPL" in tickers
    assert "MSFT" in tickers


@pytest.mark.asyncio
async def test_get_portfolio_unknown_user_returns_empty():
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio", {"user_id": "unknown"})
    data = json.loads(result.content[0].text)
    assert data["positions"] == []
    assert data["total_pl"] == 0


@pytest.mark.asyncio
async def test_get_allocation_morgan():
    async with Client(mcp) as client:
        result = await client.call_tool("get_allocation", {"user_id": "morgan"})
    data = json.loads(result.content[0].text)
    assert data["user_id"] == "morgan"
    assert len(data["allocation"]) == 4
    total_pct = sum(a["pct_of_portfolio"] for a in data["allocation"])
    assert abs(total_pct - 100.0) < 0.1
    # Sorted by weight descending
    pcts = [a["pct_of_portfolio"] for a in data["allocation"]]
    assert pcts == sorted(pcts, reverse=True)


@pytest.mark.asyncio
async def test_pl_calculation():
    """NVDA: 100 shares, cost_basis 95.40, current price 134.87 → P&L = 3947."""
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio", {"user_id": "morgan"})
    data = json.loads(result.content[0].text)
    nvda = next(p for p in data["positions"] if p["ticker"] == "NVDA")
    expected_pl = round((134.87 - 95.40) * 100, 2)
    assert nvda["pl"] == expected_pl
