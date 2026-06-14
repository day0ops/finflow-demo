import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="portfolio-agent")


class RunRequest(BaseModel):
    input: str
    session_id: str
    context: dict = {}


AGENT_CARD = {
    "name": "portfolio-agent",
    "description": "Portfolio holdings, P&L, and allocation analysis via portfolio-mcp",
    "capabilities": ["portfolio", "holdings", "pl", "allocation"],
    "framework": "google-adk",
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
    from agent import run_agent  # lazy import — avoids ADK init at module load time

    output = await run_agent(req.input, req.session_id)
    return {"output": output, "session_id": req.session_id, "agent": "portfolio-agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
