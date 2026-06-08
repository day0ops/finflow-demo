import asyncio
import json
import os

import anthropic
from tools import execute_trade_sync, get_order_status_sync, list_orders_sync

_TOOLS = [
    {
        "name": "execute_trade",
        "description": "Execute a stock trade for a user. action must be BUY or SELL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier e.g. morgan"},
                "ticker": {"type": "string", "description": "Stock symbol e.g. NVDA, AAPL"},
                "action": {"type": "string", "enum": ["BUY", "SELL"]},
                "shares": {"type": "number", "description": "Number of shares (positive)"},
            },
            "required": ["user_id", "ticker", "action", "shares"],
        },
    },
    {
        "name": "get_order_status",
        "description": "Get the status of an existing order by its order_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "8-character order ID"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_orders",
        "description": "List all orders placed by a user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
            },
            "required": ["user_id"],
        },
    },
]

_TOOL_REGISTRY = {
    "execute_trade": lambda args: execute_trade_sync(args["user_id"], args["ticker"], args["action"], args["shares"]),
    "get_order_status": lambda args: get_order_status_sync(args["order_id"]),
    "list_orders": lambda args: list_orders_sync(args["user_id"]),
}


def _run_sync(input: str, session_id: str, context: dict) -> str:
    """Synchronous Anthropic tool-use loop — called via asyncio.to_thread."""
    user_id = context.get("user_id", "morgan")
    client = anthropic.Anthropic(
        base_url=os.getenv("ANTHROPIC_BASE_URL", "http://agentgateway.finflow.svc"),
        api_key=os.getenv("LLM_API_KEY", "demo"),
    )
    model = os.getenv("LLM_MODEL", "claude-opus-4-6")
    system = (
        f"You are a trade execution agent for the FinFlow financial demo. "
        f"The current user is '{user_id}'. "
        "Use execute_trade to place BUY or SELL orders, get_order_status to check an existing order, "
        "and list_orders to review all orders for the user. "
        "Always use tools — never invent trade data or order IDs."
    )

    messages = [{"role": "user", "content": input}]
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        tools=_TOOLS,
        tool_choice={"type": "auto"},
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = _TOOL_REGISTRY.get(block.name)
                result = fn(block.input) if fn else json.dumps({"error": f"Unknown tool: {block.name}"})
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system,
            tools=_TOOLS,
            tool_choice={"type": "auto"},
            messages=messages,
        )

    return next((block.text for block in response.content if block.type == "text"), "")


async def run_agent(input: str, session_id: str, context: dict = {}) -> str:
    return await asyncio.to_thread(_run_sync, input, session_id, context)
