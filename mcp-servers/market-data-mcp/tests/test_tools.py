import json

import pytest
from fastmcp import Client
from server import mcp


@pytest.mark.asyncio
async def test_get_price_known_ticker():
    async with Client(mcp) as client:
        result = await client.call_tool("get_price", {"ticker": "NVDA"})
    data = json.loads(result.content[0].text)
    assert data["ticker"] == "NVDA"
    assert data["price"] == 134.87
    assert data["change_pct"] == 2.41
    assert "sector" in data


@pytest.mark.asyncio
async def test_get_price_lowercase_ticker():
    async with Client(mcp) as client:
        result = await client.call_tool("get_price", {"ticker": "aapl"})
    data = json.loads(result.content[0].text)
    assert data["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_get_price_unknown_ticker_raises():
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="Unknown ticker"):
            await client.call_tool("get_price", {"ticker": "FAKE"})


@pytest.mark.asyncio
async def test_get_historical_default_days():
    async with Client(mcp) as client:
        result = await client.call_tool("get_historical", {"ticker": "MSFT"})
    data = json.loads(result.content[0].text)
    assert data["ticker"] == "MSFT"
    assert len(data["history"]) == 5
    assert "date" in data["history"][0]
    assert "close" in data["history"][0]


@pytest.mark.asyncio
async def test_get_historical_limited_days():
    async with Client(mcp) as client:
        result = await client.call_tool("get_historical", {"ticker": "NVDA", "days": 3})
    data = json.loads(result.content[0].text)
    assert len(data["history"]) == 3


@pytest.mark.asyncio
async def test_get_sector_performance():
    async with Client(mcp) as client:
        result = await client.call_tool("get_sector_performance", {})
    data = json.loads(result.content[0].text)
    assert isinstance(data, list)
    assert len(data) >= 1
    sectors = [s["sector"] for s in data]
    assert "Technology" in sectors
    tech = next(s for s in data if s["sector"] == "Technology")
    assert "avg_change_pct" in tech
    assert "tickers" in tech
