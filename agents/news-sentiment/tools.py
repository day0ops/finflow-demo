import asyncio
import os

from fastmcp import Client

# Tests monkeypatch this to the news-mcp FastMCP instance
MCP_URL = os.getenv("NEWS_MCP_URL", "http://agentgateway.finflow.svc/mcp/news/mcp/")


async def _call(tool_name: str, args: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, args)
    return result.content[0].text if result.content else ""


# Async versions — used in tests
async def search_news(ticker: str, limit: int = 3) -> str:
    """Search recent news headlines for a stock ticker."""
    return await _call("search_news", {"ticker": ticker, "limit": limit})


async def get_portfolio_sentiment(tickers: list[str]) -> str:
    """Get sentiment summary for a list of tickers."""
    return await _call("get_portfolio_sentiment", {"tickers": tickers})


# Sync wrappers — used inside the Anthropic tool-use loop (called from thread, no running event loop)
def search_news_sync(ticker: str, limit: int = 3) -> str:
    """Search recent news headlines for a stock ticker."""
    return asyncio.run(search_news(ticker, limit))


def get_portfolio_sentiment_sync(tickers: list[str]) -> str:
    """Get sentiment summary for a list of tickers."""
    return asyncio.run(get_portfolio_sentiment(tickers))
