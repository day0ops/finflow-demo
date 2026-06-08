import os

from fastmcp import Client

# All MCP calls route through agentgateway.
# Tests monkeypatch this to the portfolio-mcp FastMCP instance.
MCP_URL = os.getenv("PORTFOLIO_MCP_URL", "http://agentgateway.finflow.svc/mcp/portfolio/mcp/")


async def _call(tool_name: str, args: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, args)
    return result.content[0].text if result.content else ""


async def get_portfolio(user_id: str) -> str:
    """Get portfolio holdings and P&L for a user (morgan or alex)."""
    return await _call("get_portfolio", {"user_id": user_id})


async def get_allocation(user_id: str) -> str:
    """Get portfolio allocation breakdown by ticker for a user."""
    return await _call("get_allocation", {"user_id": user_id})
