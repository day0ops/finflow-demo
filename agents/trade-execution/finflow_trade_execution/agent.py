import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools import execute_trade, get_order_status, list_orders

# Route all LLM calls through agentgateway's OpenAI-compatible endpoint.
# LiteLlm reads OPENAI_BASE_URL + OPENAI_API_KEY from environment.
os.environ.setdefault("OPENAI_BASE_URL", os.getenv("LLM_BASE_URL", "http://agentgateway.finflow.svc/v1"))
os.environ.setdefault("OPENAI_API_KEY", os.getenv("LLM_API_KEY", "demo"))

root_agent = Agent(
    name="trade-execution-agent",
    model=LiteLlm(model=os.getenv("LLM_MODEL", "openai/gpt-4o")),
    description="Stock trade execution (BUY/SELL), order status, and order history",
    instruction=(
        "You are a trade execution agent for the FinFlow financial demo. "
        "Use execute_trade to place BUY or SELL orders, get_order_status to check an existing order, "
        "and list_orders to review all orders for a user. "
        "Always use tools — never invent trade data or order IDs."
    ),
    tools=[execute_trade, get_order_status, list_orders],
)

_session_service = InMemorySessionService()
_runner = Runner(
    agent=root_agent,
    app_name="trade-execution-agent",
    session_service=_session_service,
)


async def run_agent(input: str, session_id: str, context: dict = {}) -> str:
    await _session_service.create_session(
        app_name="trade-execution-agent",
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
