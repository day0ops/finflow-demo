import json

import pytest
import store
from fastmcp import Client
from server import mcp


@pytest.fixture(autouse=True)
def reset_order_store():
    """Clear order store between tests."""
    store.ORDER_STORE._orders.clear()
    yield
    store.ORDER_STORE._orders.clear()


@pytest.mark.asyncio
async def test_execute_trade_buy():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "NVDA", "action": "BUY", "shares": 10.0},
        )
    data = json.loads(result.content[0].text)
    assert data["status"] == "FILLED"
    assert data["ticker"] == "NVDA"
    assert data["action"] == "BUY"
    assert data["shares"] == 10.0
    assert data["price"] == 134.87
    assert data["total"] == round(10.0 * 134.87, 2)
    assert "order_id" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_execute_trade_sell():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "AAPL", "action": "SELL", "shares": 5.0},
        )
    data = json.loads(result.content[0].text)
    assert data["action"] == "SELL"
    assert data["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_execute_trade_lowercase_inputs():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "msft", "action": "buy", "shares": 2.0},
        )
    data = json.loads(result.content[0].text)
    assert data["ticker"] == "MSFT"
    assert data["action"] == "BUY"


@pytest.mark.asyncio
async def test_execute_trade_invalid_action():
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="Invalid action"):
            await client.call_tool(
                "execute_trade",
                {"user_id": "morgan", "ticker": "NVDA", "action": "HOLD", "shares": 10.0},
            )


@pytest.mark.asyncio
async def test_execute_trade_negative_shares():
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="positive"):
            await client.call_tool(
                "execute_trade",
                {"user_id": "morgan", "ticker": "NVDA", "action": "BUY", "shares": -5.0},
            )


@pytest.mark.asyncio
async def test_get_order_status():
    async with Client(mcp) as client:
        buy_result = await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "NVDA", "action": "BUY", "shares": 1.0},
        )
    order_id = json.loads(buy_result.content[0].text)["order_id"]

    async with Client(mcp) as client:
        status_result = await client.call_tool("get_order_status", {"order_id": order_id})
    data = json.loads(status_result.content[0].text)
    assert data["order_id"] == order_id
    assert data["status"] == "FILLED"


@pytest.mark.asyncio
async def test_get_order_status_not_found():
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="not found"):
            await client.call_tool("get_order_status", {"order_id": "FAKE123"})


@pytest.mark.asyncio
async def test_list_orders():
    async with Client(mcp) as client:
        await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "NVDA", "action": "BUY", "shares": 10.0},
        )
        await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "AAPL", "action": "BUY", "shares": 5.0},
        )
        result = await client.call_tool("list_orders", {"user_id": "morgan"})
    data = json.loads(result.content[0].text)
    assert data["user_id"] == "morgan"
    assert len(data["orders"]) == 2
