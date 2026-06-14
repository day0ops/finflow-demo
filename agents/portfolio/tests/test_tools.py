import json

import db as db_module
import pytest
import tools as tools_module
from server import mcp as _mcp  # from portfolio-mcp/server.py (via conftest sys.path)


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    """Replace the module-level connection with a seeded in-memory DB."""
    import server

    conn = db_module.get_connection(":memory:")
    db_module.seed_db(conn)
    monkeypatch.setattr(server, "_conn", conn)
    monkeypatch.setattr(server, "_DB_PATH", ":memory:")
    yield conn
    conn.close()
    monkeypatch.setattr(server, "_conn", None)


@pytest.fixture(autouse=True)
def in_process_mcp(monkeypatch):
    """Replace HTTP MCP URL with in-process FastMCP instance."""
    monkeypatch.setattr(tools_module, "MCP_URL", _mcp)


@pytest.mark.asyncio
async def test_get_portfolio_morgan():
    result = json.loads(await tools_module.get_portfolio("morgan"))
    assert result["user_id"] == "morgan"
    tickers = [p["ticker"] for p in result["positions"]]
    assert "NVDA" in tickers
    assert "MSFT" in tickers
    assert len(result["positions"]) == 4


@pytest.mark.asyncio
async def test_get_portfolio_alex():
    result = json.loads(await tools_module.get_portfolio("alex"))
    assert result["user_id"] == "alex"
    assert len(result["positions"]) == 2


@pytest.mark.asyncio
async def test_get_allocation_morgan():
    result = json.loads(await tools_module.get_allocation("morgan"))
    assert result["user_id"] == "morgan"
    assert "allocation" in result
    tickers = [a["ticker"] for a in result["allocation"]]
    assert "NVDA" in tickers


def test_health():
    import agent_server  # alias for the agent's server.py (registered by conftest)
    from fastapi.testclient import TestClient

    with TestClient(agent_server.app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_card():
    import agent_server  # alias for the agent's server.py (registered by conftest)
    from fastapi.testclient import TestClient

    with TestClient(agent_server.app) as client:
        response = client.get("/.well-known/agent-card.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "portfolio-agent"
    assert data["framework"] == "google-adk"
    assert "capabilities" in data


@pytest.mark.asyncio
async def test_run_endpoint():
    import sys
    import types as _types
    from unittest.mock import AsyncMock

    import agent_server  # alias for the agent's server.py (registered by conftest)
    from fastapi.testclient import TestClient

    # server.py does `from agent import run_agent` lazily inside the route handler.
    # Rather than importing the real agent module (which requires litellm), inject a
    # lightweight fake module into sys.modules so the lazy import resolves to it.
    fake_agent = _types.ModuleType("agent")
    fake_agent.run_agent = AsyncMock(return_value="morgan holds NVDA, MSFT, AAPL, GOOGL")
    sys.modules["agent"] = fake_agent
    try:
        with TestClient(agent_server.app) as client:
            response = client.post(
                "/run",
                json={
                    "input": "What is morgan's portfolio?",
                    "session_id": "test-1",
                    "context": {},
                },
            )
    finally:
        sys.modules.pop("agent", None)

    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "morgan holds NVDA, MSFT, AAPL, GOOGL"
    assert data["session_id"] == "test-1"
    assert data["agent"] == "portfolio-agent"
