import asyncio
import os

import httpx

MARKET_DATA_AGENT_URL = os.getenv("MARKET_DATA_AGENT_URL", "http://market-data-agent:8000")
PORTFOLIO_AGENT_URL = os.getenv("PORTFOLIO_AGENT_URL", "http://portfolio-agent:8000")
NEWS_SENTIMENT_AGENT_URL = os.getenv("NEWS_SENTIMENT_AGENT_URL", "http://news-sentiment-agent:8000")
TRADE_EXECUTION_AGENT_URL = os.getenv("TRADE_EXECUTION_AGENT_URL", "http://trade-execution-agent:8000")


async def _call_agent(client: httpx.AsyncClient, url: str, input: str, session_id: str, context: dict) -> str:
    response = await client.post(
        f"{url}/run",
        json={"input": input, "session_id": session_id, "context": context},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["output"]


async def dispatch_briefing(input: str, session_id: str, context: dict) -> str:
    agents = [
        ("market-data-agent", MARKET_DATA_AGENT_URL),
        ("portfolio-agent", PORTFOLIO_AGENT_URL),
        ("news-sentiment-agent", NEWS_SENTIMENT_AGENT_URL),
    ]
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_call_agent(client, url, input, session_id, context) for _, url in agents],
            return_exceptions=True,
        )
    errors = [(name, str(err)) for (name, _), err in zip(agents, results) if isinstance(err, Exception)]
    if errors:
        raise RuntimeError(f"Downstream agents failed: {errors}")
    return "\n\n".join(str(r) for r in results)


async def dispatch_trade(input: str, session_id: str, context: dict) -> str:
    async with httpx.AsyncClient() as client:
        return await _call_agent(client, TRADE_EXECUTION_AGENT_URL, input, session_id, context)
