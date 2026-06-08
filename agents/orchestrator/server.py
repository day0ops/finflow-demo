import uvicorn
from dispatch import dispatch_briefing, dispatch_trade
from fastapi import FastAPI, HTTPException
from intent import Intent, detect_intent
from pydantic import BaseModel

app = FastAPI(title="finflow-orchestrator")


class RunRequest(BaseModel):
    input: str
    session_id: str
    context: dict = {}


AGENT_CARD = {
    "name": "finflow-orchestrator",
    "description": "Intent-driven orchestrator — routes briefing and trade requests to sub-agents in parallel",
    "capabilities": ["orchestration", "portfolio-briefing", "trade-routing"],
    "framework": "custom",
    "authentication": {"type": "bearer", "scheme": "obo"},
}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/.well-known/agent.json")
async def agent_card():
    return AGENT_CARD


@app.post("/run")
async def run(req: RunRequest):
    intent = detect_intent(req.input)
    if intent == Intent.BRIEFING:
        output = await dispatch_briefing(req.input, req.session_id, req.context)
    elif intent == Intent.TRADE:
        output = await dispatch_trade(req.input, req.session_id, req.context)
    else:
        raise HTTPException(
            status_code=422,
            detail="Could not determine intent. Try asking for a portfolio overview or to execute a trade.",
        )
    return {"output": output, "session_id": req.session_id, "agent": "finflow-orchestrator"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
