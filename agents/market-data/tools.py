import os

from fastmcp import Client

# All MCP calls route through agentgateway — never directly to market-data-mcp.
# Tests monkeypatch this to the FastMCP instance for in-process execution.
MCP_URL = os.getenv("MARKET_DATA_MCP_URL", "http://agentgateway.finflow.svc/mcp/market-data/mcp/")


async def _call(tool_name: str, args: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, args)
    return result.content[0].text if result.content else ""


async def get_price(ticker: str) -> str:
    """Get current price and daily change for a stock ticker (NVDA, AAPL, MSFT, GOOGL, AMZN)."""
    return await _call("get_price", {"ticker": ticker})


async def get_historical(ticker: str, days: int = 5) -> str:
    """Get historical closing prices for a ticker. days: number of trading days (max 5)."""
    return await _call("get_historical", {"ticker": ticker, "days": days})


async def get_sector_performance() -> str:
    """Get aggregated sector performance across all tracked tickers."""
    return await _call("get_sector_performance", {})
