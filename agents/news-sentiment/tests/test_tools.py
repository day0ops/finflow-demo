import json
import sys
import types

import pytest
import tools as tools_module
from server import mcp as _mcp  # news-mcp's server (via conftest sys.path)


@pytest.fixture(autouse=True)
def in_process_mcp(monkeypatch):
    """Replace HTTP MCP URL with in-process FastMCP instance."""
    monkeypatch.setattr(tools_module, "MCP_URL", _mcp)


@pytest.mark.asyncio
async def test_search_news_nvda():
    result = json.loads(await tools_module.search_news("NVDA"))
    assert result["ticker"] == "NVDA"
    assert len(result["articles"]) == 3
    assert "headline" in result["articles"][0]
    assert "score" in result["articles"][0]


@pytest.mark.asyncio
async def test_search_news_limit():
    result = json.loads(await tools_module.search_news("NVDA", limit=2))
    assert len(result["articles"]) == 2


@pytest.mark.asyncio
async def test_search_news_case_insensitive():
    result = json.loads(await tools_module.search_news("nvda"))
    assert result["ticker"] == "NVDA"
    assert len(result["articles"]) > 0


@pytest.mark.asyncio
async def test_get_portfolio_sentiment():
    result = json.loads(await tools_module.get_portfolio_sentiment(["NVDA", "MSFT"]))
    tickers_in_result = [t["ticker"] for t in result["tickers"]]
    assert "NVDA" in tickers_in_result
    assert "MSFT" in tickers_in_result
    assert "overall_sentiment" in result
    msft = next(t for t in result["tickers"] if t["ticker"] == "MSFT")
    assert msft["sentiment"] == "positive"


def test_health():
    import agent_server
    from fastapi.testclient import TestClient

    with TestClient(agent_server.app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_card():
    import agent_server
    from fastapi.testclient import TestClient

    with TestClient(agent_server.app) as client:
        response = client.get("/.well-known/agent-card.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "news-sentiment-agent"
    assert data["framework"] == "anthropic-sdk"
    assert "capabilities" in data


@pytest.mark.asyncio
async def test_run_endpoint():
    from unittest.mock import AsyncMock

    from fastapi.testclient import TestClient

    # server.py does `from agent import run_agent` lazily inside the route handler.
    # Rather than importing the real agent module (which requires anthropic), inject a
    # lightweight fake module into sys.modules so the lazy import resolves to it.
    fake_agent = types.ModuleType("agent")
    fake_agent.run_agent = AsyncMock(return_value="NVDA sentiment: positive")
    sys.modules["agent"] = fake_agent
    try:
        import agent_server

        with TestClient(agent_server.app) as client:
            response = client.post(
                "/run",
                json={"input": "NVDA sentiment?", "session_id": "s1", "context": {}},
            )
    finally:
        sys.modules.pop("agent", None)

    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "NVDA sentiment: positive"
    assert data["session_id"] == "s1"
    assert data["agent"] == "news-sentiment-agent"
