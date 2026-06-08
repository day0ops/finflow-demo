import os
from trace import TraceCapture

import httpx
from fastapi import APIRouter
from models import ChatRequest, ChatResponse, ElicitationData, PolicyEvent

from routes.policies import _state as policy_state

router = APIRouter()

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

_TRADE_KEYWORDS = {"trade", "buy", "sell", "execute", "purchase", "shares"}
_BRIEFING_KEYWORDS = {
    "portfolio",
    "briefing",
    "holdings",
    "performance",
    "overview",
    "picture",
    "context",
    "news",
}
_GUARDRAIL_PHRASES = {"guaranteed", "sure profit", "risk-free", "100% return"}


def _detect_intent(text: str) -> str:
    words = set(text.lower().split())
    if words & _TRADE_KEYWORDS:
        return "trade"
    if words & _BRIEFING_KEYWORDS:
        return "briefing"
    return "unknown"


def _agents_for_intent(intent: str) -> list[str]:
    if intent == "briefing":
        return ["market-data-agent", "portfolio-agent", "news-sentiment-agent"]
    if intent == "trade":
        return ["trade-execution-agent"]
    return []


@router.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    intent = _detect_intent(req.message)
    tc = TraceCapture(intent)

    # Guardrails
    if policy_state.guardrails:
        msg_lower = req.message.lower()
        if any(phrase in msg_lower for phrase in _GUARDRAIL_PHRASES):
            tc.add_policy_event(
                PolicyEvent(
                    type="guardrail",
                    policy="Guardrails",
                    verdict="deny",
                    message="Message contains prohibited financial advice language",
                )
            )
            tc.status_code = 400
            return ChatResponse(
                message="Request blocked: prohibited financial advice language detected.",
                trace=tc.build(),
            )
        tc.add_policy_event(
            PolicyEvent(
                type="guardrail",
                policy="Guardrails",
                verdict="allow",
                message="No prohibited content detected",
            )
        )

    # Rate limit (demo: always allow, visible in trace)
    if policy_state.rate_limit:
        tc.add_policy_event(
            PolicyEvent(
                type="rate_limit",
                policy="Rate Limits",
                verdict="allow",
                message="10 req/min — budget ok (1/10 used)",
            )
        )

    # RBAC — block trade intent
    if policy_state.rbac and intent == "trade":
        tc.add_policy_event(
            PolicyEvent(
                type="rbac_block",
                policy="MCP RBAC",
                verdict="deny",
                message="TRADE agent requires 'trade' role — current role: viewer",
            )
        )
        tc.status_code = 403
        return ChatResponse(
            message="Request denied. Your role does not have TRADE permissions. Contact your administrator.",
            trace=tc.build(),
        )

    # Elicitation gate — unconfirmed trade
    if policy_state.elicitation and intent == "trade" and not req.confirmed:
        tc.add_policy_event(
            PolicyEvent(
                type="elicitation_required",
                policy="Elicitation",
                verdict="allow",
                message="Trade execution requires explicit user confirmation",
            )
        )
        return ChatResponse(
            message="Confirmation required before executing this trade.",
            trace=tc.build(),
            elicitation=ElicitationData(
                prompt=f"Confirm: {req.message}",
                trade_details=f"Executing: {req.message}. This will be sent to the trade-execution agent.",
            ),
        )

    # Proxy to orchestrator
    for agent in _agents_for_intent(intent):
        tc.add_agent(agent)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{ORCHESTRATOR_URL}/run",
                json={"input": req.message, "session_id": req.session_id, "context": {}},
                timeout=60.0,
            )
            resp.raise_for_status()
            output = resp.json()["output"]
            tc.status_code = 200
    except httpx.HTTPStatusError as exc:
        tc.status_code = exc.response.status_code
        return ChatResponse(
            message=f"Orchestrator returned {exc.response.status_code}.",
            trace=tc.build(),
        )
    except httpx.HTTPError:
        tc.status_code = 503
        return ChatResponse(
            message="Could not reach the orchestrator. Is it running?",
            trace=tc.build(),
        )

    return ChatResponse(message=output, trace=tc.build())
