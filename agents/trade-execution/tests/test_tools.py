import json
import sys
import types

import pytest


@pytest.mark.asyncio
async def test_execute_trade_buy():
    import tools as tools_module

    result = json.loads(await tools_module.execute_trade("morgan", "NVDA", "BUY", 10))
    assert result["status"] == "FILLED"
    assert result["ticker"] == "NVDA"
    assert result["action"] == "BUY"
    assert result["shares"] == 10
    assert "order_id" in result


@pytest.mark.asyncio
async def test_execute_trade_sell():
    import tools as tools_module

    result = json.loads(await tools_module.execute_trade("morgan", "AAPL", "SELL", 5))
    assert result["status"] == "FILLED"
    assert result["action"] == "SELL"


@pytest.mark.asyncio
async def test_get_order_status():
    import tools as tools_module

    order = json.loads(await tools_module.execute_trade("morgan", "MSFT", "BUY", 2))
    order_id = order["order_id"]
    status = json.loads(await tools_module.get_order_status(order_id))
    assert status["order_id"] == order_id
    assert status["status"] == "FILLED"


@pytest.mark.asyncio
async def test_execute_trade_invalid_action_raises():
    import tools as tools_module

    with pytest.raises(Exception):
        await tools_module.execute_trade("morgan", "NVDA", "HOLD", 10)


def test_health():
    import agent_server
    from fastapi.testclient import TestClient

    with TestClient(agent_server.app) as client:
        response = client.get("/health")
    assert response.status_code == 200


def test_agent_card():
    import agent_server
    from fastapi.testclient import TestClient

    with TestClient(agent_server.app) as client:
        response = client.get("/.well-known/agent-card.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "trade-execution-agent"
    assert data["framework"] == "anthropic-sdk"


@pytest.mark.asyncio
async def test_run_endpoint():
    from fastapi.testclient import TestClient

    fake_agent = types.ModuleType("agent")

    async def fake_run_agent(input, session_id, context={}):
        return "Order NVDA BUY 10 filled"

    fake_agent.run_agent = fake_run_agent
    sys.modules["agent"] = fake_agent

    try:
        import agent_server

        with TestClient(agent_server.app) as client:
            response = client.post(
                "/run",
                json={"input": "buy 10 NVDA", "session_id": "s1", "context": {"user_id": "morgan"}},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "Order NVDA BUY 10 filled"
        assert data["session_id"] == "s1"
        assert data["agent"] == "trade-execution-agent"
    finally:
        sys.modules.pop("agent", None)
