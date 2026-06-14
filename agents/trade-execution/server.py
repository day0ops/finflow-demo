import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="trade-execution-agent")


class RunRequest(BaseModel):
    input: str
    session_id: str
    context: dict = {}


AGENT_CARD = {
    "name": "trade-execution-agent",
    "description": "Trade validation and submission via brokerage-mcp (subject to RBAC and elicitation at gateway)",
    "capabilities": ["trading", "order-execution", "order-status"],
    "framework": "anthropic-sdk",
    "authentication": {"type": "bearer", "scheme": "obo"},
}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/.well-known/agent-card.json")
async def agent_card():
    return AGENT_CARD


@app.post("/run")
async def run(req: RunRequest):
    from agent import run_agent

    output = await run_agent(req.input, req.session_id, req.context)
    return {"output": output, "session_id": req.session_id, "agent": "trade-execution-agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
