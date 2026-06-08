import asyncio
import json
import os

import anthropic
from tools import get_portfolio_sentiment_sync, search_news_sync

_TOOLS = [
    {
        "name": "search_news",
        "description": "Search recent news headlines for a stock ticker. Returns headlines with sentiment scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock symbol e.g. NVDA, AAPL, MSFT"},
                "limit": {
                    "type": "integer",
                    "description": "Max articles to return (default 3)",
                    "default": 3,
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_portfolio_sentiment",
        "description": "Get aggregated sentiment summary for a list of stock tickers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": 'List of stock symbols e.g. ["NVDA", "AAPL"]',
                },
            },
            "required": ["tickers"],
        },
    },
]

_TOOL_REGISTRY = {
    "search_news": lambda args: search_news_sync(args["ticker"], args.get("limit", 3)),
    "get_portfolio_sentiment": lambda args: get_portfolio_sentiment_sync(args["tickers"]),
}


def _run_sync(input: str, session_id: str) -> str:
    """Synchronous Anthropic tool-use loop — called via asyncio.to_thread."""
    client = anthropic.Anthropic(
        base_url=os.getenv("ANTHROPIC_BASE_URL", "http://agentgateway.finflow.svc"),
        api_key=os.getenv("LLM_API_KEY", "demo"),
    )
    model = os.getenv("LLM_MODEL", "claude-opus-4-6")
    system = (
        "You are a news and sentiment analysis agent for the FinFlow financial demo. "
        "Use search_news to get headlines for individual tickers and get_portfolio_sentiment "
        "for a multi-ticker sentiment overview. Always use tools — never invent news data."
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


async def run_agent(input: str, session_id: str) -> str:
    return await asyncio.to_thread(_run_sync, input, session_id)
