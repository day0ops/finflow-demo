import json

import pytest
import tools as tools_module
from server import mcp as _mcp  # from market-data-mcp/server.py (via conftest sys.path)


@pytest.fixture(autouse=True)
def in_process_mcp(monkeypatch):
    """Replace HTTP MCP URL with in-process FastMCP instance."""
    monkeypatch.setattr(tools_module, "MCP_URL", _mcp)


@pytest.mark.asyncio
async def test_get_price_nvda():
    result = json.loads(await tools_module.get_price("NVDA"))
    assert result["ticker"] == "NVDA"
    assert result["price"] == 134.87
    assert result["change_pct"] == 2.41
    assert "sector" in result


@pytest.mark.asyncio
async def test_get_price_case_insensitive():
    result = json.loads(await tools_module.get_price("aapl"))
    assert result["ticker"] == "AAPL"
    assert result["price"] == 211.50


@pytest.mark.asyncio
async def test_get_historical_default_days():
    result = json.loads(await tools_module.get_historical("MSFT"))
    assert result["ticker"] == "MSFT"
    assert len(result["history"]) == 5
    assert "date" in result["history"][0]
    assert "close" in result["history"][0]


@pytest.mark.asyncio
async def test_get_historical_limited_days():
    result = json.loads(await tools_module.get_historical("NVDA", 3))
    assert len(result["history"]) == 3


@pytest.mark.asyncio
async def test_get_sector_performance():
    result = json.loads(await tools_module.get_sector_performance())
    assert isinstance(result, list)
    sectors = [s["sector"] for s in result]
    assert "Technology" in sectors


# ── server endpoint tests ────────────────────────────────────────────────────────


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
    assert data["name"] == "market-data-agent"
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
    fake_agent.run_agent = AsyncMock(return_value="NVDA is at $134.87")
    sys.modules["agent"] = fake_agent
    try:
        with TestClient(agent_server.app) as client:
            response = client.post("/run", json={"input": "What is NVDA price?", "session_id": "test-1", "context": {}})
    finally:
        sys.modules.pop("agent", None)

    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "NVDA is at $134.87"
    assert data["session_id"] == "test-1"
    assert data["agent"] == "market-data-agent"
