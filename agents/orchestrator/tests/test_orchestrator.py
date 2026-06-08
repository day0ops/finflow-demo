import httpx
import pytest
import respx
from fastapi.testclient import TestClient

# ── intent tests ────────────────────────────────────────────────────────────────


def test_detect_intent_briefing_words():
    from intent import Intent, detect_intent

    assert detect_intent("Give me a full picture of my portfolio") == Intent.BRIEFING
    assert detect_intent("Show my holdings") == Intent.BRIEFING
    assert detect_intent("portfolio performance overview") == Intent.BRIEFING


def test_detect_intent_trade_words():
    from intent import Intent, detect_intent

    assert detect_intent("Buy 100 shares of NVDA") == Intent.TRADE
    assert detect_intent("Execute the NVDA trade") == Intent.TRADE
    assert detect_intent("sell AAPL") == Intent.TRADE


def test_detect_intent_trade_beats_briefing():
    from intent import Intent, detect_intent

    # "buy" wins over "portfolio" if both present
    assert detect_intent("buy shares from my portfolio") == Intent.TRADE


def test_detect_intent_unknown():
    from intent import Intent, detect_intent

    assert detect_intent("hello") == Intent.UNKNOWN


# ── dispatch tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_dispatch_briefing_calls_three_agents():
    import os

    os.environ.setdefault("MARKET_DATA_AGENT_URL", "http://market-data-agent:8000")
    os.environ.setdefault("PORTFOLIO_AGENT_URL", "http://portfolio-agent:8000")
    os.environ.setdefault("NEWS_SENTIMENT_AGENT_URL", "http://news-sentiment-agent:8000")

    respx.post("http://market-data-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "prices ok", "session_id": "s1", "agent": "market-data-agent"})
    )
    respx.post("http://portfolio-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "holdings ok", "session_id": "s1", "agent": "portfolio-agent"})
    )
    respx.post("http://news-sentiment-agent:8000/run").mock(
        return_value=httpx.Response(
            200, json={"output": "news ok", "session_id": "s1", "agent": "news-sentiment-agent"}
        )
    )

    from dispatch import dispatch_briefing

    result = await dispatch_briefing("Give me a portfolio briefing", "s1", {})
    assert "prices ok" in result
    assert "holdings ok" in result
    assert "news ok" in result


@pytest.mark.asyncio
@respx.mock
async def test_dispatch_trade_calls_one_agent():
    import os

    os.environ.setdefault("TRADE_EXECUTION_AGENT_URL", "http://trade-execution-agent:8000")

    respx.post("http://trade-execution-agent:8000/run").mock(
        return_value=httpx.Response(
            200,
            json={"output": "trade executed", "session_id": "s1", "agent": "trade-execution-agent"},
        )
    )

    from dispatch import dispatch_trade

    result = await dispatch_trade("Buy 100 NVDA", "s1", {})
    assert "trade executed" in result


# ── server endpoint tests ────────────────────────────────────────────────────────


def test_health():
    from server import app

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_card():
    from server import app

    with TestClient(app) as client:
        response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "finflow-orchestrator"
    assert data["framework"] == "custom"
    assert "capabilities" in data
    assert "authentication" in data


@respx.mock
def test_run_trade_intent():
    import os

    os.environ["TRADE_EXECUTION_AGENT_URL"] = "http://trade-execution-agent:8000"
    respx.post("http://trade-execution-agent:8000/run").mock(
        return_value=httpx.Response(
            200,
            json={"output": "trade executed", "session_id": "s1", "agent": "trade-execution-agent"},
        )
    )
    from server import app

    with TestClient(app) as client:
        response = client.post("/run", json={"input": "buy 10 NVDA", "session_id": "s1", "context": {}})
    assert response.status_code == 200
    assert "trade executed" in response.json()["output"]


def test_run_unknown_intent_returns_422():
    from server import app

    with TestClient(app) as client:
        response = client.post("/run", json={"input": "hello there", "session_id": "s1", "context": {}})
    assert response.status_code == 422


def test_detect_intent_order_is_unknown():
    from intent import Intent, detect_intent

    assert detect_intent("show my order history") == Intent.UNKNOWN


@pytest.mark.asyncio
@respx.mock
async def test_dispatch_briefing_raises_on_agent_failure():
    import os

    os.environ.setdefault("MARKET_DATA_AGENT_URL", "http://market-data-agent:8000")
    os.environ.setdefault("PORTFOLIO_AGENT_URL", "http://portfolio-agent:8000")
    os.environ.setdefault("NEWS_SENTIMENT_AGENT_URL", "http://news-sentiment-agent:8000")

    respx.post("http://market-data-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "prices ok", "session_id": "s1", "agent": "market-data-agent"})
    )
    respx.post("http://portfolio-agent:8000/run").mock(return_value=httpx.Response(500, text="Internal Server Error"))
    respx.post("http://news-sentiment-agent:8000/run").mock(
        return_value=httpx.Response(
            200, json={"output": "news ok", "session_id": "s1", "agent": "news-sentiment-agent"}
        )
    )

    from dispatch import dispatch_briefing

    with pytest.raises(RuntimeError, match="portfolio-agent"):
        await dispatch_briefing("Give me a portfolio briefing", "s1", {})


@respx.mock
def test_run_briefing_intent():
    import os

    os.environ.setdefault("MARKET_DATA_AGENT_URL", "http://market-data-agent:8000")
    os.environ.setdefault("PORTFOLIO_AGENT_URL", "http://portfolio-agent:8000")
    os.environ.setdefault("NEWS_SENTIMENT_AGENT_URL", "http://news-sentiment-agent:8000")

    respx.post("http://market-data-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "prices ok", "session_id": "s1", "agent": "market-data-agent"})
    )
    respx.post("http://portfolio-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "holdings ok", "session_id": "s1", "agent": "portfolio-agent"})
    )
    respx.post("http://news-sentiment-agent:8000/run").mock(
        return_value=httpx.Response(
            200, json={"output": "news ok", "session_id": "s1", "agent": "news-sentiment-agent"}
        )
    )

    from server import app

    with TestClient(app) as client:
        response = client.post("/run", json={"input": "show my portfolio holdings", "session_id": "s1", "context": {}})
    assert response.status_code == 200
    data = response.json()
    assert "prices ok" in data["output"]
    assert "holdings ok" in data["output"]
    assert "news ok" in data["output"]
