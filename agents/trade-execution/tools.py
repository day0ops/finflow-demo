import asyncio
import os

from fastmcp import Client

MCP_URL = os.getenv("BROKERAGE_MCP_URL", "http://agentgateway.finflow.svc/mcp/brokerage/mcp/")


async def _call(tool_name: str, args: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, args)
    return result.content[0].text if result.content else ""


async def execute_trade(user_id: str, ticker: str, action: str, shares: float) -> str:
    """Execute a stock trade. action must be BUY or SELL. Returns order confirmation with order_id."""
    return await _call("execute_trade", {"user_id": user_id, "ticker": ticker, "action": action, "shares": shares})


async def get_order_status(order_id: str) -> str:
    """Get the status of an order by its order_id."""
    return await _call("get_order_status", {"order_id": order_id})


async def list_orders(user_id: str) -> str:
    """List all orders for a user."""
    return await _call("list_orders", {"user_id": user_id})


# Sync wrappers — used inside the Anthropic tool-use loop (called from thread)
def execute_trade_sync(user_id: str, ticker: str, action: str, shares: float) -> str:
    """Execute a stock trade. action must be BUY or SELL."""
    return asyncio.run(execute_trade(user_id, ticker, action, shares))


def get_order_status_sync(order_id: str) -> str:
    """Get the status of an order by its order_id."""
    return asyncio.run(get_order_status(order_id))


def list_orders_sync(user_id: str) -> str:
    """List all orders for a user."""
    return asyncio.run(list_orders(user_id))
