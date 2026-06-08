import json

import pytest
from fastmcp import Client
from server import mcp


@pytest.mark.asyncio
async def test_search_news_known_ticker():
    async with Client(mcp) as client:
        result = await client.call_tool("search_news", {"ticker": "NVDA"})
    data = json.loads(result.content[0].text)
    assert data["ticker"] == "NVDA"
    assert len(data["articles"]) == 3
    assert "headline" in data["articles"][0]
    assert "sentiment" in data["articles"][0]
    assert "score" in data["articles"][0]


@pytest.mark.asyncio
async def test_search_news_limit():
    async with Client(mcp) as client:
        result = await client.call_tool("search_news", {"ticker": "NVDA", "limit": 1})
    data = json.loads(result.content[0].text)
    assert len(data["articles"]) == 1


@pytest.mark.asyncio
async def test_search_news_lowercase():
    async with Client(mcp) as client:
        result = await client.call_tool("search_news", {"ticker": "msft"})
    data = json.loads(result.content[0].text)
    assert data["ticker"] == "MSFT"
    assert len(data["articles"]) >= 1


@pytest.mark.asyncio
async def test_search_news_unknown_ticker():
    async with Client(mcp) as client:
        result = await client.call_tool("search_news", {"ticker": "FAKE"})
    data = json.loads(result.content[0].text)
    assert data["articles"] == []


@pytest.mark.asyncio
async def test_get_portfolio_sentiment():
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio_sentiment", {"tickers": ["NVDA", "MSFT", "AAPL"]})
    data = json.loads(result.content[0].text)
    assert len(data["tickers"]) == 3
    ticker_names = [t["ticker"] for t in data["tickers"]]
    assert "NVDA" in ticker_names
    assert "MSFT" in ticker_names
    assert "overall_score" in data
    assert data["overall_sentiment"] in ("positive", "negative", "neutral")


@pytest.mark.asyncio
async def test_msft_sentiment_is_positive():
    """MSFT has two positive articles — should score positive."""
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio_sentiment", {"tickers": ["MSFT"]})
    data = json.loads(result.content[0].text)
    msft = data["tickers"][0]
    assert msft["sentiment"] == "positive"
    assert msft["avg_score"] > 0.3
