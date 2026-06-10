import os

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .mcp_tools import get_mcp_tools
from .openai_model import OpenAICompatibleLlm

mcp_tools = get_mcp_tools()

root_agent = Agent(
    name="portfolio-agent",
    model=OpenAICompatibleLlm(model=os.getenv("LLM_MODEL", "gpt-4o")),
    description="Portfolio holdings, P&L, and allocation analysis",
    instruction=(
        "You are a portfolio analysis agent for the FinFlow financial demo. "
        "Use get_portfolio to retrieve a user's holdings and P&L summary, "
        "and get_allocation to see how the portfolio is distributed across tickers. "
        "Always use tools — never invent portfolio data or prices."
    ),
    tools=mcp_tools,
)

_session_service = InMemorySessionService()
_runner = Runner(
    agent=root_agent,
    app_name="portfolio-agent",
    session_service=_session_service,
)


async def run_agent(input: str, session_id: str) -> str:
    await _session_service.create_session(
        app_name="portfolio-agent",
        user_id=session_id,
        session_id=session_id,
    )
    message = types.Content(role="user", parts=[types.Part(text=input)])
    final_response = ""
    async for event in _runner.run_async(user_id=session_id, session_id=session_id, new_message=message):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
    return final_response
