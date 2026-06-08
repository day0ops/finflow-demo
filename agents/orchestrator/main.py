import asyncio

from bedrock_agentcore import BedrockAgentCoreApp
from dispatch import dispatch_briefing, dispatch_trade
from intent import Intent, detect_intent

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    input_text = payload.get("input", "")
    session_id = payload.get("session_id", "default")
    context = payload.get("context", {})
    intent = detect_intent(input_text)
    if intent == Intent.BRIEFING:
        output = asyncio.run(dispatch_briefing(input_text, session_id, context))
    elif intent == Intent.TRADE:
        output = asyncio.run(dispatch_trade(input_text, session_id, context))
    else:
        return {
            "error": "Could not determine intent. Try asking for a portfolio overview or to execute a trade.",
            "session_id": session_id,
        }
    return {"output": output, "session_id": session_id, "agent": "finflow-orchestrator"}


if __name__ == "__main__":
    app.run()
