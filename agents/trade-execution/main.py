import asyncio

from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    from agent import run_agent  # lazy import

    input_text = payload.get("input", "")
    session_id = payload.get("session_id", "default")
    context = payload.get("context", {})
    output = asyncio.run(run_agent(input_text, session_id, context))
    return {"output": output, "session_id": session_id, "agent": "trade-execution-agent"}


if __name__ == "__main__":
    app.run()
