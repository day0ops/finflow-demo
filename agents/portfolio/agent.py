import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools import get_allocation, get_portfolio

# Route all LLM calls through agentgateway's OpenAI-compatible endpoint.
# LiteLlm reads OPENAI_BASE_URL + OPENAI_API_KEY from environment.
os.environ.setdefault("OPENAI_BASE_URL", os.getenv("LLM_BASE_URL", "http://agentgateway.finflow.svc/v1"))
os.environ.setdefault("OPENAI_API_KEY", os.getenv("LLM_API_KEY", "demo"))

_root_agent = Agent(
    name="portfolio-agent",
    model=LiteLlm(model=os.getenv("LLM_MODEL", "openai/gpt-4o")),
    description="Portfolio holdings, P&L, and allocation analysis",
    instruction=(
        "You are a portfolio analysis agent for the FinFlow financial demo. "
        "Use get_portfolio to retrieve a user's holdings and P&L summary, "
        "and get_allocation to see how the portfolio is distributed across tickers. "
        "Always use tools — never invent portfolio data or prices."
    ),
    tools=[get_portfolio, get_allocation],
)

_session_service = InMemorySessionService()
_runner = Runner(
    agent=_root_agent,
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
