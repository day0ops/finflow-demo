# FinFlow Phase 2: Agents — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build all five FinFlow agents (orchestrator, market-data, portfolio, news-sentiment, trade-execution) as tested, containerized HTTP services exposing the A2A interface. Three agents (orchestrator, market-data, portfolio) run on the kagent runtime via Google ADK + LiteLlm. Two agents (news-sentiment, trade-execution) use AgentCore (Anthropic tool-use loop). All LLM calls and all MCP calls route through agentgateway — no direct provider or MCP server access from agents.

**Architecture:** Each agent is a FastAPI server exposing `POST /run`, `GET /health`, and `GET /.well-known/agent.json`. The `finflow-orchestrator` is deterministic (no LLM). kagent runtime agents use ADK + LiteLlm → agw OpenAI-compat endpoint. AgentCore agents use Anthropic SDK → agw Anthropic-compat endpoint. All MCP tool calls route through agw (`http://agentgateway.finflow.svc/mcp/<server>/mcp/`). Tests monkeypatch MCP_URL to in-process FastMCP — no agw or LLM needed in CI.

**Tech Stack:** Python 3.12, uv, FastAPI 0.115, uvicorn, pydantic 2, httpx 0.27, fastmcp>=2.0, google-adk>=2.2 (kagent agents), anthropic>=0.106 (AgentCore agents), respx>=0.21, pytest, pytest-asyncio

---

## File Map

```
agents/
├── orchestrator/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── server.py          # FastAPI app — POST /run, GET /health, GET /.well-known/agent.json
│   ├── intent.py          # detect_intent(text) → "briefing" | "trade" | "unknown"
│   ├── dispatch.py        # dispatch_briefing(), dispatch_trade() via httpx
│   └── tests/
│       ├── __init__.py
│       └── test_orchestrator.py
├── market-data/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── server.py          # FastAPI app
│   ├── agent.py           # Google ADK Agent + LiteLlm (kagent runtime)
│   ├── tools.py           # Async MCP wrappers + sync wrappers for ADK
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py    # sys.path + in-process MCP fixture
│       └── test_tools.py
├── portfolio/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── server.py          # FastAPI app
│   ├── agent.py           # Google ADK Agent + Runner (asyncio.to_thread)
│   ├── tools.py           # Async + sync-wrapper MCP tools (ADK requires sync)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py    # sys.path + in-memory SQLite + in-process MCP fixture
│       └── test_tools.py
├── news-sentiment/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── server.py          # FastAPI app
│   ├── agent.py           # Anthropic tool-use loop (asyncio.to_thread)
│   ├── tools.py           # Async MCP wrappers
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py    # sys.path + in-process MCP fixture
│       └── test_tools.py
└── trade-execution/
    ├── pyproject.toml
    ├── Dockerfile
    ├── server.py          # FastAPI app
    ├── agent.py           # Anthropic tool-use loop (AgentCore runtime)
    ├── tools.py           # Async MCP wrappers + sync wrappers for Anthropic loop
    └── tests/
        ├── __init__.py
        ├── conftest.py    # sys.path + reset order store + in-process MCP fixture
        └── test_tools.py

infra/k8s/base/agents/
├── kustomization.yaml
├── orchestrator.yaml
├── market-data-agent.yaml
├── portfolio-agent.yaml
├── news-sentiment-agent.yaml
└── trade-execution-agent.yaml
```

---

## Shared patterns

### A2A interface (all agents)

Every agent exposes:
```
POST /run            body: {input: str, session_id: str, context: dict}
                     response: {output: str, session_id: str, agent: str}
GET  /health         response: {"status": "ok"}
GET  /.well-known/agent.json  response: agent card JSON
```

### MCP monkeypatch fixture pattern (sub-agent tests)

`fastmcp.Client` accepts either a URL string or a `FastMCP` instance. Tests monkeypatch `MCP_URL` in the tools module to the imported in-process FastMCP instance so no HTTP server is needed.

```python
# tests/conftest.py pattern
import sys, os
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(REPO_ROOT, "mcp-servers", "<mcp-dir>"))
```

```python
# test file fixture pattern
import pytest
from server import mcp as _mcp_instance
import tools as tools_module

@pytest.fixture(autouse=True)
def in_process_mcp(monkeypatch):
    monkeypatch.setattr(tools_module, "MCP_URL", _mcp_instance)
```

---

## Task 1: finflow-orchestrator

**Files:**
- Create: `agents/orchestrator/pyproject.toml`
- Create: `agents/orchestrator/Dockerfile`
- Create: `agents/orchestrator/intent.py`
- Create: `agents/orchestrator/dispatch.py`
- Create: `agents/orchestrator/server.py`
- Create: `agents/orchestrator/tests/__init__.py`
- Create: `agents/orchestrator/tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

Create `agents/orchestrator/tests/__init__.py` (empty).

Create `agents/orchestrator/tests/test_orchestrator.py`:

```python
import pytest
import respx
import httpx
from fastapi.testclient import TestClient


# ── intent tests ────────────────────────────────────────────────────────────────

def test_detect_intent_briefing_words():
    from intent import detect_intent, Intent
    assert detect_intent("Give me a full picture of my portfolio") == Intent.BRIEFING
    assert detect_intent("Show my holdings") == Intent.BRIEFING
    assert detect_intent("portfolio performance overview") == Intent.BRIEFING

def test_detect_intent_trade_words():
    from intent import detect_intent, Intent
    assert detect_intent("Buy 100 shares of NVDA") == Intent.TRADE
    assert detect_intent("Execute the NVDA trade") == Intent.TRADE
    assert detect_intent("sell AAPL") == Intent.TRADE

def test_detect_intent_trade_beats_briefing():
    from intent import detect_intent, Intent
    # "buy" wins over "portfolio" if both present
    assert detect_intent("buy shares from my portfolio") == Intent.TRADE

def test_detect_intent_unknown():
    from intent import detect_intent, Intent
    assert detect_intent("hello") == Intent.UNKNOWN


# ── dispatch tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_dispatch_briefing_calls_three_agents():
    import os
    os.environ.setdefault("MARKET_DATA_AGENT_URL", "http://market-data-agent:8000")
    os.environ.setdefault("PORTFOLIO_AGENT_URL", "http://portfolio-agent:8000")
    os.environ.setdefault("NEWS_SENTIMENT_AGENT_URL", "http://news-sentiment-agent:8000")

    respx.post("http://market-data-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "prices ok", "session_id": "s1", "agent": "market-data-agent"})
    )
    respx.post("http://portfolio-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "holdings ok", "session_id": "s1", "agent": "portfolio-agent"})
    )
    respx.post("http://news-sentiment-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "news ok", "session_id": "s1", "agent": "news-sentiment-agent"})
    )

    from dispatch import dispatch_briefing
    result = await dispatch_briefing("Give me a portfolio briefing", "s1", {})
    assert "prices ok" in result
    assert "holdings ok" in result
    assert "news ok" in result


@pytest.mark.asyncio
@respx.mock
async def test_dispatch_trade_calls_one_agent():
    import os
    os.environ.setdefault("TRADE_EXECUTION_AGENT_URL", "http://trade-execution-agent:8000")

    respx.post("http://trade-execution-agent:8000/run").mock(
        return_value=httpx.Response(200, json={"output": "trade executed", "session_id": "s1", "agent": "trade-execution-agent"})
    )

    from dispatch import dispatch_trade
    result = await dispatch_trade("Buy 100 NVDA", "s1", {})
    assert "trade executed" in result


# ── server endpoint tests ────────────────────────────────────────────────────────

def test_health():
    from server import app
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_card():
    from server import app
    with TestClient(app) as client:
        response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "finflow-orchestrator"
    assert data["framework"] == "kagent"
    assert "capabilities" in data
    assert "authentication" in data
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd agents/orchestrator
uv run pytest tests/ -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'intent'` or similar — confirms tests reference not-yet-created code.

- [ ] **Step 3: Create pyproject.toml**

Create `agents/orchestrator/pyproject.toml`:

```toml
[project]
name = "finflow-orchestrator"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "httpx>=0.27.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "respx>=0.21.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 4: Create intent.py**

Create `agents/orchestrator/intent.py`:

```python
from enum import Enum

class Intent(str, Enum):
    BRIEFING = "briefing"
    TRADE = "trade"
    UNKNOWN = "unknown"

_TRADE_KEYWORDS = {"trade", "buy", "sell", "execute", "purchase", "order", "shares"}
_BRIEFING_KEYWORDS = {"portfolio", "briefing", "holdings", "performance", "overview", "picture", "context", "news"}

def detect_intent(text: str) -> Intent:
    words = set(text.lower().split())
    if words & _TRADE_KEYWORDS:
        return Intent.TRADE
    if words & _BRIEFING_KEYWORDS:
        return Intent.BRIEFING
    return Intent.UNKNOWN
```

- [ ] **Step 5: Create dispatch.py**

Create `agents/orchestrator/dispatch.py`:

```python
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
    async with httpx.AsyncClient() as client:
        outputs = await asyncio.gather(
            _call_agent(client, MARKET_DATA_AGENT_URL, input, session_id, context),
            _call_agent(client, PORTFOLIO_AGENT_URL, input, session_id, context),
            _call_agent(client, NEWS_SENTIMENT_AGENT_URL, input, session_id, context),
        )
    return "\n\n".join(outputs)


async def dispatch_trade(input: str, session_id: str, context: dict) -> str:
    async with httpx.AsyncClient() as client:
        return await _call_agent(client, TRADE_EXECUTION_AGENT_URL, input, session_id, context)
```

- [ ] **Step 6: Create server.py**

Create `agents/orchestrator/server.py`:

```python
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from intent import detect_intent, Intent
from dispatch import dispatch_briefing, dispatch_trade

app = FastAPI(title="finflow-orchestrator")


class RunRequest(BaseModel):
    input: str
    session_id: str
    context: dict = {}


AGENT_CARD = {
    "name": "finflow-orchestrator",
    "description": "Intent-driven orchestrator — parses user requests and dispatches in parallel to market-data, portfolio, news-sentiment, and trade-execution agents",
    "capabilities": ["orchestration", "portfolio-briefing", "trade-routing"],
    "framework": "kagent",
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
        raise HTTPException(status_code=422, detail="Could not determine intent. Try asking for a portfolio overview or to execute a trade.")
    return {"output": output, "session_id": req.session_id, "agent": "finflow-orchestrator"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 7: Create Dockerfile**

Create `agents/orchestrator/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
```

- [ ] **Step 8: Install deps and run tests**

```bash
cd agents/orchestrator
uv sync
uv run pytest tests/ -v
```

Expected output:
```
tests/test_orchestrator.py::test_detect_intent_briefing_words PASSED
tests/test_orchestrator.py::test_detect_intent_trade_words PASSED
tests/test_orchestrator.py::test_detect_intent_trade_beats_briefing PASSED
tests/test_orchestrator.py::test_detect_intent_unknown PASSED
tests/test_orchestrator.py::test_dispatch_briefing_calls_three_agents PASSED
tests/test_orchestrator.py::test_dispatch_trade_calls_one_agent PASSED
tests/test_orchestrator.py::test_health PASSED
tests/test_orchestrator.py::test_agent_card PASSED
8 passed
```

- [ ] **Step 9: Commit**

```bash
git add agents/orchestrator/
git commit -m "feat: add finflow-orchestrator with intent parsing and parallel A2A dispatch"
```

---

## Task 2: market-data-agent (Google ADK / kagent runtime)

**Files:**
- Create: `agents/market-data/pyproject.toml`
- Create: `agents/market-data/Dockerfile`
- Create: `agents/market-data/tools.py`
- Create: `agents/market-data/agent.py`
- Create: `agents/market-data/server.py`
- Create: `agents/market-data/tests/__init__.py`
- Create: `agents/market-data/tests/conftest.py`
- Create: `agents/market-data/tests/test_tools.py`

- [ ] **Step 1: Write the failing tests**

Create `agents/market-data/tests/__init__.py` (empty).

Create `agents/market-data/tests/conftest.py`:

```python
import sys
import os

# Add market-data-mcp to path so tests can import its FastMCP instance
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(REPO_ROOT, "mcp-servers", "market-data-mcp"))
```

Create `agents/market-data/tests/test_tools.py`:

```python
import json
import pytest
from server import mcp as _mcp  # from market-data-mcp/server.py (via conftest sys.path)
import tools as tools_module


@pytest.fixture(autouse=True)
def in_process_mcp(monkeypatch):
    """Replace HTTP MCP URL with in-process FastMCP instance."""
    monkeypatch.setattr(tools_module, "MCP_URL", _mcp)


@pytest.mark.asyncio
async def test_get_price_nvda():
    result = json.loads(await tools_module.get_price("NVDA"))
    assert result["ticker"] == "NVDA"
    assert result["price"] == 134.87
    assert result["change_pct"] == 2.41
    assert "sector" in result


@pytest.mark.asyncio
async def test_get_price_case_insensitive():
    result = json.loads(await tools_module.get_price("aapl"))
    assert result["ticker"] == "AAPL"
    assert result["price"] == 211.50


@pytest.mark.asyncio
async def test_get_historical_default_days():
    result = json.loads(await tools_module.get_historical("MSFT"))
    assert result["ticker"] == "MSFT"
    assert len(result["history"]) == 5
    assert "date" in result["history"][0]
    assert "close" in result["history"][0]


@pytest.mark.asyncio
async def test_get_historical_limited_days():
    result = json.loads(await tools_module.get_historical("NVDA", 3))
    assert len(result["history"]) == 3


@pytest.mark.asyncio
async def test_get_sector_performance():
    result = json.loads(await tools_module.get_sector_performance())
    assert isinstance(result, list)
    sectors = [s["sector"] for s in result]
    assert "Technology" in sectors


# ── server endpoint tests ────────────────────────────────────────────────────────

def test_health():
    from fastapi.testclient import TestClient
    from server import app
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_card():
    from fastapi.testclient import TestClient
    from server import app
    with TestClient(app) as client:
        response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "market-data-agent"
    assert data["framework"] == "kagent"
    assert "capabilities" in data
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd agents/market-data
uv run pytest tests/ -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'tools'` — confirms code not yet written.

- [ ] **Step 3: Create pyproject.toml**

Create `agents/market-data/pyproject.toml`:

```toml
[project]
name = "market-data-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.0.0",
    "fastmcp>=2.0",
    "google-adk>=2.2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 4: Create tools.py**

Create `agents/market-data/tools.py`:

```python
import asyncio
import os
from fastmcp import Client

# All MCP calls route through agentgateway — never directly to market-data-mcp.
# Tests monkeypatch this to the FastMCP instance for in-process execution.
MCP_URL = os.getenv("MARKET_DATA_MCP_URL", "http://agentgateway.finflow.svc/mcp/market-data/mcp/")


async def _call(tool_name: str, args: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, args)
    return result.content[0].text


# Async versions — used in tests
async def get_price(ticker: str) -> str:
    """Get current price and daily change for a stock ticker (NVDA, AAPL, MSFT, GOOGL, AMZN)."""
    return await _call("get_price", {"ticker": ticker})


async def get_historical(ticker: str, days: int = 5) -> str:
    """Get historical closing prices for a ticker. days: number of trading days (max 5)."""
    return await _call("get_historical", {"ticker": ticker, "days": days})


async def get_sector_performance() -> str:
    """Get aggregated sector performance across all tracked tickers."""
    return await _call("get_sector_performance", {})


# Sync wrappers — required by ADK (tools run in thread pool via asyncio.to_thread)
def get_price_sync(ticker: str) -> str:
    """Get current price and daily change for a stock ticker (NVDA, AAPL, MSFT, GOOGL, AMZN)."""
    return asyncio.run(get_price(ticker))


def get_historical_sync(ticker: str, days: int = 5) -> str:
    """Get historical closing prices for a ticker. days: number of trading days (max 5)."""
    return asyncio.run(get_historical(ticker, days))


def get_sector_performance_sync() -> str:
    """Get aggregated sector performance across all tracked tickers."""
    return asyncio.run(get_sector_performance())
```

- [ ] **Step 5: Create agent.py**

Create `agents/market-data/agent.py`:

```python
import asyncio
import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools import get_price_sync, get_historical_sync, get_sector_performance_sync

# Route all LLM calls through agentgateway's OpenAI-compatible endpoint.
# LiteLlm reads OPENAI_BASE_URL + OPENAI_API_KEY from environment.
os.environ.setdefault("OPENAI_BASE_URL", os.getenv("LLM_BASE_URL", "http://agentgateway.finflow.svc/v1"))
os.environ.setdefault("OPENAI_API_KEY", os.getenv("LLM_API_KEY", "demo"))

_root_agent = Agent(
    name="market-data-agent",
    model=LiteLlm(model=os.getenv("LLM_MODEL", "openai/gpt-4o")),
    description="Market prices, historical data, and sector performance",
    instruction=(
        "You are a market data agent for the FinFlow financial demo. "
        "Use get_price_sync for current prices, get_historical_sync for price history, "
        "and get_sector_performance_sync for sector breakdown. "
        "Always use tools — never invent prices or data."
    ),
    tools=[get_price_sync, get_historical_sync, get_sector_performance_sync],
)

_session_service = InMemorySessionService()
_runner = Runner(
    agent=_root_agent,
    app_name="market-data-agent",
    session_service=_session_service,
)


def _run_sync(input: str, session_id: str) -> str:
    """Synchronous ADK runner — called via asyncio.to_thread from async context."""
    _session_service.create_session(
        app_name="market-data-agent",
        user_id="default",
        session_id=session_id,
    )
    message = types.Content(role="user", parts=[types.Part(text=input)])
    final_response = ""
    for event in _runner.run(user_id="default", session_id=session_id, new_message=message):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
    return final_response


async def run_agent(input: str, session_id: str) -> str:
    return await asyncio.to_thread(_run_sync, input, session_id)
```

- [ ] **Step 6: Create server.py**

Create `agents/market-data/server.py`:

```python
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(title="market-data-agent")


class RunRequest(BaseModel):
    input: str
    session_id: str
    context: dict = {}


AGENT_CARD = {
    "name": "market-data-agent",
    "description": "Real-time market prices, historical data, and sector performance via market-data-mcp",
    "capabilities": ["market-data", "prices", "sectors", "historical"],
    "framework": "kagent",
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
    output = await run_agent(req.input, req.session_id)
    return {"output": output, "session_id": req.session_id, "agent": "market-data-agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 7: Create Dockerfile**

Create `agents/market-data/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
```

- [ ] **Step 8: Install deps and run tests**

```bash
cd agents/market-data
uv sync
uv run pytest tests/ -v
```

Expected output:
```
tests/test_tools.py::test_get_price_nvda PASSED
tests/test_tools.py::test_get_price_case_insensitive PASSED
tests/test_tools.py::test_get_historical_default_days PASSED
tests/test_tools.py::test_get_historical_limited_days PASSED
tests/test_tools.py::test_get_sector_performance PASSED
tests/test_tools.py::test_health PASSED
tests/test_tools.py::test_agent_card PASSED
7 passed
```

- [ ] **Step 9: Commit**

```bash
git add agents/market-data/
git commit -m "feat: add market-data-agent with Google ADK agent (kagent runtime) and market-data-mcp tools"
```

---

## Task 3: portfolio-agent (Google ADK)

**Files:**
- Create: `agents/portfolio/pyproject.toml`
- Create: `agents/portfolio/Dockerfile`
- Create: `agents/portfolio/tools.py`
- Create: `agents/portfolio/agent.py`
- Create: `agents/portfolio/server.py`
- Create: `agents/portfolio/tests/__init__.py`
- Create: `agents/portfolio/tests/conftest.py`
- Create: `agents/portfolio/tests/test_tools.py`

- [ ] **Step 1: Write the failing tests**

Create `agents/portfolio/tests/__init__.py` (empty).

Create `agents/portfolio/tests/conftest.py`:

```python
import sys
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(REPO_ROOT, "mcp-servers", "portfolio-mcp"))


@pytest.fixture(autouse=True)
def setup_portfolio_mcp(monkeypatch):
    """Create in-memory SQLite DB, seed it, patch portfolio-mcp server, and use in-process MCP."""
    import db as portfolio_db
    import server as portfolio_server
    import tools as tools_module

    conn = portfolio_db.get_connection(":memory:")
    portfolio_db.seed_db(conn)

    monkeypatch.setattr(portfolio_server, "_conn", conn)
    monkeypatch.setattr(portfolio_server, "_DB_PATH", ":memory:")
    monkeypatch.setattr(tools_module, "MCP_URL", portfolio_server.mcp)

    yield
    conn.close()
    monkeypatch.setattr(portfolio_server, "_conn", None)
```

Create `agents/portfolio/tests/test_tools.py`:

```python
import json
import pytest
import tools as tools_module


@pytest.mark.asyncio
async def test_get_portfolio_morgan():
    result = json.loads(await tools_module.get_portfolio("morgan"))
    assert result["user_id"] == "morgan"
    tickers = [p["ticker"] for p in result["positions"]]
    assert "NVDA" in tickers
    assert "MSFT" in tickers
    assert len(result["positions"]) == 4


@pytest.mark.asyncio
async def test_get_portfolio_alex():
    result = json.loads(await tools_module.get_portfolio("alex"))
    assert result["user_id"] == "alex"
    assert len(result["positions"]) == 2


@pytest.mark.asyncio
async def test_get_allocation_morgan():
    result = json.loads(await tools_module.get_allocation("morgan"))
    assert result["user_id"] == "morgan"
    assert "allocation" in result
    tickers = [a["ticker"] for a in result["allocation"]]
    assert "NVDA" in tickers


# ── server endpoint tests ────────────────────────────────────────────────────────

def test_health():
    from fastapi.testclient import TestClient
    from server import app
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_card():
    from fastapi.testclient import TestClient
    from server import app
    with TestClient(app) as client:
        response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "portfolio-agent"
    assert data["framework"] == "adk"
    assert "capabilities" in data
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd agents/portfolio
uv run pytest tests/ -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'tools'`

- [ ] **Step 3: Create pyproject.toml**

Create `agents/portfolio/pyproject.toml`:

```toml
[project]
name = "portfolio-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.0.0",
    "fastmcp>=2.0",
    "google-adk>=2.2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 4: Create tools.py**

Create `agents/portfolio/tools.py`:

```python
import asyncio
import os
from fastmcp import Client

# Tests monkeypatch this to the portfolio-mcp FastMCP instance
MCP_URL = os.getenv("PORTFOLIO_MCP_URL", "http://agentgateway.finflow.svc/mcp/portfolio/mcp/")


async def _call(tool_name: str, args: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, args)
    return result.content[0].text


# Async versions — used in tests
async def get_portfolio(user_id: str) -> str:
    """Get portfolio holdings and P&L for a user (morgan or alex)."""
    return await _call("get_portfolio", {"user_id": user_id})


async def get_allocation(user_id: str) -> str:
    """Get portfolio allocation breakdown by ticker for a user."""
    return await _call("get_allocation", {"user_id": user_id})


# Sync wrappers — used as ADK tool functions (called from thread pool via asyncio.to_thread)
def get_portfolio_sync(user_id: str) -> str:
    """Get portfolio holdings and P&L for a user (morgan or alex)."""
    return asyncio.run(get_portfolio(user_id))


def get_allocation_sync(user_id: str) -> str:
    """Get portfolio allocation breakdown by ticker for a user."""
    return asyncio.run(get_allocation(user_id))
```

- [ ] **Step 5: Create agent.py**

Create `agents/portfolio/agent.py`:

```python
import asyncio
import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools import get_portfolio_sync, get_allocation_sync

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
        "Use get_portfolio_sync to retrieve holdings and P&L. "
        "Use get_allocation_sync to retrieve allocation percentages. "
        "Always use tools — never invent portfolio data."
    ),
    tools=[get_portfolio_sync, get_allocation_sync],
)

_session_service = InMemorySessionService()
_runner = Runner(
    agent=_root_agent,
    app_name="portfolio-agent",
    session_service=_session_service,
)


def _run_sync(input: str, session_id: str) -> str:
    """Synchronous ADK runner — called via asyncio.to_thread from async context."""
    _session_service.create_session(
        app_name="portfolio-agent",
        user_id="default",
        session_id=session_id,
    )
    message = types.Content(role="user", parts=[types.Part(text=input)])
    final_response = ""
    for event in _runner.run(user_id="default", session_id=session_id, new_message=message):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
    return final_response


async def run_agent(input: str, session_id: str) -> str:
    return await asyncio.to_thread(_run_sync, input, session_id)
```

- [ ] **Step 6: Create server.py**

Create `agents/portfolio/server.py`:

```python
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(title="portfolio-agent")


class RunRequest(BaseModel):
    input: str
    session_id: str
    context: dict = {}


AGENT_CARD = {
    "name": "portfolio-agent",
    "description": "Portfolio holdings, P&L, and allocation analysis via portfolio-mcp",
    "capabilities": ["portfolio", "holdings", "pl", "allocation"],
    "framework": "adk",
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
    output = await run_agent(req.input, req.session_id)
    return {"output": output, "session_id": req.session_id, "agent": "portfolio-agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 7: Create Dockerfile**

Create `agents/portfolio/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
```

- [ ] **Step 8: Install deps and run tests**

```bash
cd agents/portfolio
uv sync
uv run pytest tests/ -v
```

Expected output:
```
tests/test_tools.py::test_get_portfolio_morgan PASSED
tests/test_tools.py::test_get_portfolio_alex PASSED
tests/test_tools.py::test_get_allocation_morgan PASSED
tests/test_tools.py::test_health PASSED
tests/test_tools.py::test_agent_card PASSED
5 passed
```

- [ ] **Step 9: Commit**

```bash
git add agents/portfolio/
git commit -m "feat: add portfolio-agent with Google ADK agent and portfolio-mcp tools"
```

---

## Task 4: news-sentiment-agent (Anthropic)

**Files:**
- Create: `agents/news-sentiment/pyproject.toml`
- Create: `agents/news-sentiment/Dockerfile`
- Create: `agents/news-sentiment/tools.py`
- Create: `agents/news-sentiment/agent.py`
- Create: `agents/news-sentiment/server.py`
- Create: `agents/news-sentiment/tests/__init__.py`
- Create: `agents/news-sentiment/tests/conftest.py`
- Create: `agents/news-sentiment/tests/test_tools.py`

- [ ] **Step 1: Write the failing tests**

Create `agents/news-sentiment/tests/__init__.py` (empty).

Create `agents/news-sentiment/tests/conftest.py`:

```python
import sys
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(REPO_ROOT, "mcp-servers", "news-mcp"))
```

Create `agents/news-sentiment/tests/test_tools.py`:

```python
import json
import pytest
from server import mcp as _mcp  # from news-mcp/server.py
import tools as tools_module


@pytest.fixture(autouse=True)
def in_process_mcp(monkeypatch):
    monkeypatch.setattr(tools_module, "MCP_URL", _mcp)


@pytest.mark.asyncio
async def test_search_news_nvda():
    result = json.loads(await tools_module.search_news("NVDA"))
    assert result["ticker"] == "NVDA"
    assert len(result["articles"]) == 3
    assert "headline" in result["articles"][0]
    assert "score" in result["articles"][0]


@pytest.mark.asyncio
async def test_search_news_limit():
    result = json.loads(await tools_module.search_news("NVDA", limit=2))
    assert len(result["articles"]) == 2


@pytest.mark.asyncio
async def test_search_news_case_insensitive():
    result = json.loads(await tools_module.search_news("nvda"))
    assert result["ticker"] == "NVDA"
    assert len(result["articles"]) > 0


@pytest.mark.asyncio
async def test_get_portfolio_sentiment():
    result = json.loads(await tools_module.get_portfolio_sentiment(["NVDA", "MSFT"]))
    tickers_in_result = [t["ticker"] for t in result["tickers"]]
    assert "NVDA" in tickers_in_result
    assert "MSFT" in tickers_in_result
    assert "overall_sentiment" in result
    msft = next(t for t in result["tickers"] if t["ticker"] == "MSFT")
    assert msft["sentiment"] == "positive"


# ── server endpoint tests ────────────────────────────────────────────────────────

def test_health():
    from fastapi.testclient import TestClient
    from server import app
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200


def test_agent_card():
    from fastapi.testclient import TestClient
    from server import app
    with TestClient(app) as client:
        response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "news-sentiment-agent"
    assert data["framework"] == "agentcore"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd agents/news-sentiment
uv run pytest tests/ -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'tools'`

- [ ] **Step 3: Create pyproject.toml**

Create `agents/news-sentiment/pyproject.toml`:

```toml
[project]
name = "news-sentiment-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.0.0",
    "fastmcp>=2.0",
    "anthropic>=0.106.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 4: Create tools.py**

Create `agents/news-sentiment/tools.py`:

```python
import asyncio
import json
import os
from fastmcp import Client

# Tests monkeypatch this to the news-mcp FastMCP instance
MCP_URL = os.getenv("NEWS_MCP_URL", "http://agentgateway.finflow.svc/mcp/news/mcp/")


async def _call(tool_name: str, args: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, args)
    return result.content[0].text


# Async versions — used in tests
async def search_news(ticker: str, limit: int = 3) -> str:
    """Search recent news headlines for a stock ticker."""
    return await _call("search_news", {"ticker": ticker, "limit": limit})


async def get_portfolio_sentiment(tickers: list[str]) -> str:
    """Get sentiment summary for a list of tickers."""
    return await _call("get_portfolio_sentiment", {"tickers": tickers})


# Sync wrappers — used inside the Anthropic tool-use loop (called from thread)
def search_news_sync(ticker: str, limit: int = 3) -> str:
    """Search recent news headlines for a stock ticker."""
    return asyncio.run(search_news(ticker, limit))


def get_portfolio_sentiment_sync(tickers: list[str]) -> str:
    """Get sentiment summary for a list of tickers."""
    return asyncio.run(get_portfolio_sentiment(tickers))
```

- [ ] **Step 5: Create agent.py**

Create `agents/news-sentiment/agent.py`:

```python
import asyncio
import json
import os
import anthropic
from tools import search_news_sync, get_portfolio_sentiment_sync

_TOOLS = [
    {
        "name": "search_news",
        "description": "Search recent news headlines for a stock ticker. Returns list of headlines with sentiment scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock symbol e.g. NVDA, AAPL, MSFT"},
                "limit": {"type": "integer", "description": "Max articles to return (default 3)", "default": 3},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_portfolio_sentiment",
        "description": "Get aggregated sentiment summary for a list of stock tickers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stock symbols e.g. [\"NVDA\", \"AAPL\"]",
                },
            },
            "required": ["tickers"],
        },
    },
]

_TOOL_REGISTRY = {
    "search_news": lambda args: search_news_sync(args["ticker"], args.get("limit", 3)),
    "get_portfolio_sentiment": lambda args: get_portfolio_sentiment_sync(args["tickers"]),
}


def _run_sync(input: str, session_id: str) -> str:
    """Synchronous Anthropic tool-use loop — called via asyncio.to_thread from async context."""
    # Route through agentgateway's Anthropic-compatible endpoint.
    # ANTHROPIC_BASE_URL must point to agw (e.g. http://agentgateway.finflow.svc).
    # Never call api.anthropic.com directly.
    client = anthropic.Anthropic(
        base_url=os.getenv("ANTHROPIC_BASE_URL", "http://agentgateway.finflow.svc"),
        api_key=os.getenv("LLM_API_KEY", "demo"),
    )
    model = os.getenv("LLM_MODEL", "claude-opus-4-6")
    system = (
        "You are a news and sentiment analysis agent for the FinFlow financial demo. "
        "Use search_news to get headlines for individual tickers and get_portfolio_sentiment "
        "for a multi-ticker sentiment overview. Always use tools — never invent news data."
    )

    messages = [{"role": "user", "content": input}]
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        tools=_TOOLS,
        tool_choice={"type": "auto"},
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = _TOOL_REGISTRY.get(block.name)
                result = fn(block.input) if fn else json.dumps({"error": f"Unknown tool: {block.name}"})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system,
            tools=_TOOLS,
            tool_choice={"type": "auto"},
            messages=messages,
        )

    return next((block.text for block in response.content if block.type == "text"), "")


async def run_agent(input: str, session_id: str) -> str:
    return await asyncio.to_thread(_run_sync, input, session_id)
```

- [ ] **Step 6: Create server.py**

Create `agents/news-sentiment/server.py`:

```python
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(title="news-sentiment-agent")


class RunRequest(BaseModel):
    input: str
    session_id: str
    context: dict = {}


AGENT_CARD = {
    "name": "news-sentiment-agent",
    "description": "News headlines and sentiment analysis per holding via news-mcp",
    "capabilities": ["news", "sentiment", "headlines"],
    "framework": "agentcore",
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
    output = await run_agent(req.input, req.session_id)
    return {"output": output, "session_id": req.session_id, "agent": "news-sentiment-agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 7: Create Dockerfile**

Create `agents/news-sentiment/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
```

- [ ] **Step 8: Install deps and run tests**

```bash
cd agents/news-sentiment
uv sync
uv run pytest tests/ -v
```

Expected output:
```
tests/test_tools.py::test_search_news_nvda PASSED
tests/test_tools.py::test_search_news_limit PASSED
tests/test_tools.py::test_search_news_case_insensitive PASSED
tests/test_tools.py::test_get_portfolio_sentiment PASSED
tests/test_tools.py::test_health PASSED
tests/test_tools.py::test_agent_card PASSED
6 passed
```

- [ ] **Step 9: Commit**

```bash
git add agents/news-sentiment/
git commit -m "feat: add news-sentiment-agent with Anthropic tool-use loop and news-mcp tools"
```

---

## Task 5: trade-execution-agent (Anthropic / AgentCore runtime)

**Files:**
- Create: `agents/trade-execution/pyproject.toml`
- Create: `agents/trade-execution/Dockerfile`
- Create: `agents/trade-execution/tools.py`
- Create: `agents/trade-execution/agent.py`
- Create: `agents/trade-execution/server.py`
- Create: `agents/trade-execution/tests/__init__.py`
- Create: `agents/trade-execution/tests/conftest.py`
- Create: `agents/trade-execution/tests/test_tools.py`

- [ ] **Step 1: Write the failing tests**

Create `agents/trade-execution/tests/__init__.py` (empty).

Create `agents/trade-execution/tests/conftest.py`:

```python
import sys
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(REPO_ROOT, "mcp-servers", "brokerage-mcp"))
```

Create `agents/trade-execution/tests/test_tools.py`:

```python
import json
import pytest
from server import mcp as _mcp  # from brokerage-mcp/server.py
import store as brokerage_store  # from brokerage-mcp/store.py
import tools as tools_module


@pytest.fixture(autouse=True)
def setup_brokerage_mcp(monkeypatch):
    brokerage_store.ORDER_STORE._orders.clear()
    monkeypatch.setattr(tools_module, "MCP_URL", _mcp)
    yield
    brokerage_store.ORDER_STORE._orders.clear()


@pytest.mark.asyncio
async def test_execute_trade_buy():
    result = json.loads(await tools_module.execute_trade("morgan", "NVDA", "BUY", 10))
    assert result["status"] == "FILLED"
    assert result["ticker"] == "NVDA"
    assert result["action"] == "BUY"
    assert result["shares"] == 10
    assert "order_id" in result


@pytest.mark.asyncio
async def test_execute_trade_sell():
    result = json.loads(await tools_module.execute_trade("morgan", "AAPL", "SELL", 5))
    assert result["status"] == "FILLED"
    assert result["action"] == "SELL"


@pytest.mark.asyncio
async def test_get_order_status():
    order = json.loads(await tools_module.execute_trade("morgan", "MSFT", "BUY", 2))
    order_id = order["order_id"]
    status = json.loads(await tools_module.get_order_status(order_id))
    assert status["order_id"] == order_id
    assert status["status"] == "FILLED"


@pytest.mark.asyncio
async def test_execute_trade_invalid_action_raises():
    with pytest.raises(Exception):
        await tools_module.execute_trade("morgan", "NVDA", "HOLD", 10)


# ── server endpoint tests ────────────────────────────────────────────────────────

def test_health():
    from fastapi.testclient import TestClient
    from server import app
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200


def test_agent_card():
    from fastapi.testclient import TestClient
    from server import app
    with TestClient(app) as client:
        response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "trade-execution-agent"
    assert data["framework"] == "agentcore"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd agents/trade-execution
uv run pytest tests/ -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'tools'`

- [ ] **Step 3: Create pyproject.toml**

Create `agents/trade-execution/pyproject.toml`:

```toml
[project]
name = "trade-execution-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.0.0",
    "fastmcp>=2.0",
    "anthropic>=0.106.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 4: Create tools.py**

Create `agents/trade-execution/tools.py`:

```python
import asyncio
import os
from fastmcp import Client

# All MCP calls route through agentgateway — never directly to brokerage-mcp.
# Tests monkeypatch this to the FastMCP instance for in-process execution.
MCP_URL = os.getenv("BROKERAGE_MCP_URL", "http://agentgateway.finflow.svc/mcp/brokerage/mcp/")


async def _call(tool_name: str, args: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, args)
    return result.content[0].text


# Async versions — used in tests
async def execute_trade(user_id: str, ticker: str, action: str, shares: float) -> str:
    """Execute a stock trade. action must be BUY or SELL. Returns order confirmation with order_id."""
    return await _call("execute_trade", {
        "user_id": user_id,
        "ticker": ticker,
        "action": action,
        "shares": shares,
    })


async def get_order_status(order_id: str) -> str:
    """Get the status of an order by its order_id."""
    return await _call("get_order_status", {"order_id": order_id})


async def list_orders(user_id: str) -> str:
    """List all orders for a user."""
    return await _call("list_orders", {"user_id": user_id})


# Sync wrappers — used inside the Anthropic tool-use loop (called from thread)
def execute_trade_sync(user_id: str, ticker: str, action: str, shares: float) -> str:
    """Execute a stock trade. action must be BUY or SELL."""
    return asyncio.run(execute_trade(user_id, ticker, action, shares))


def get_order_status_sync(order_id: str) -> str:
    """Get the status of an order by its order_id."""
    return asyncio.run(get_order_status(order_id))


def list_orders_sync(user_id: str) -> str:
    """List all orders for a user."""
    return asyncio.run(list_orders(user_id))
```

- [ ] **Step 5: Create agent.py**

Create `agents/trade-execution/agent.py`:

```python
import asyncio
import json
import os
import anthropic
from tools import execute_trade_sync, get_order_status_sync, list_orders_sync

_TOOLS = [
    {
        "name": "execute_trade",
        "description": "Execute a stock trade for a user. action must be BUY or SELL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier e.g. morgan"},
                "ticker": {"type": "string", "description": "Stock symbol e.g. NVDA, AAPL"},
                "action": {"type": "string", "enum": ["BUY", "SELL"]},
                "shares": {"type": "number", "description": "Number of shares (positive)"},
            },
            "required": ["user_id", "ticker", "action", "shares"],
        },
    },
    {
        "name": "get_order_status",
        "description": "Get the status of an existing order by its order_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "8-character order ID"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_orders",
        "description": "List all orders placed by a user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
            },
            "required": ["user_id"],
        },
    },
]

_TOOL_REGISTRY = {
    "execute_trade": lambda args: execute_trade_sync(
        args["user_id"], args["ticker"], args["action"], args["shares"]
    ),
    "get_order_status": lambda args: get_order_status_sync(args["order_id"]),
    "list_orders": lambda args: list_orders_sync(args["user_id"]),
}


def _run_sync(input: str, session_id: str, context: dict) -> str:
    """Synchronous Anthropic tool-use loop — called via asyncio.to_thread from async context."""
    user_id = context.get("user_id", "morgan")
    client = anthropic.Anthropic(
        base_url=os.getenv("ANTHROPIC_BASE_URL", "http://agentgateway.finflow.svc"),
        api_key=os.getenv("LLM_API_KEY", "demo"),
    )
    model = os.getenv("LLM_MODEL", "claude-opus-4-6")
    system = (
        "You are a trade execution agent for the FinFlow financial demo. "
        f"The current user is '{user_id}'. "
        "Use execute_trade to submit trades and get_order_status to confirm them. "
        "Always use tools — never invent order confirmations."
    )

    messages = [{"role": "user", "content": input}]
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        tools=_TOOLS,
        tool_choice={"type": "auto"},
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = _TOOL_REGISTRY.get(block.name)
                result = fn(block.input) if fn else json.dumps({"error": f"Unknown tool: {block.name}"})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system,
            tools=_TOOLS,
            tool_choice={"type": "auto"},
            messages=messages,
        )

    return next((block.text for block in response.content if block.type == "text"), "")


async def run_agent(input: str, session_id: str, context: dict = {}) -> str:
    return await asyncio.to_thread(_run_sync, input, session_id, context)
```

- [ ] **Step 6: Create server.py**

Create `agents/trade-execution/server.py`:

```python
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(title="trade-execution-agent")


class RunRequest(BaseModel):
    input: str
    session_id: str
    context: dict = {}


AGENT_CARD = {
    "name": "trade-execution-agent",
    "description": "Trade validation and submission via brokerage-mcp (subject to RBAC and elicitation at gateway)",
    "capabilities": ["trading", "order-execution", "order-status"],
    "framework": "agentcore",
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
    output = await run_agent(req.input, req.session_id, req.context)
    return {"output": output, "session_id": req.session_id, "agent": "trade-execution-agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 7: Create Dockerfile**

Create `agents/trade-execution/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
```

- [ ] **Step 8: Install deps and run tests**

```bash
cd agents/trade-execution
uv sync
uv run pytest tests/ -v
```

Expected output:
```
tests/test_tools.py::test_execute_trade_buy PASSED
tests/test_tools.py::test_execute_trade_sell PASSED
tests/test_tools.py::test_get_order_status PASSED
tests/test_tools.py::test_execute_trade_invalid_action_raises PASSED
tests/test_tools.py::test_health PASSED
tests/test_tools.py::test_agent_card PASSED
6 passed
```

- [ ] **Step 9: Commit**

```bash
git add agents/trade-execution/
git commit -m "feat: add trade-execution-agent with Anthropic tool-use loop and brokerage-mcp via agentgateway"
```

---

## Task 6: K8s manifests for agents

**Files:**
- Create: `infra/k8s/base/agents/kustomization.yaml`
- Create: `infra/k8s/base/agents/orchestrator.yaml`
- Create: `infra/k8s/base/agents/market-data-agent.yaml`
- Create: `infra/k8s/base/agents/portfolio-agent.yaml`
- Create: `infra/k8s/base/agents/news-sentiment-agent.yaml`
- Create: `infra/k8s/base/agents/trade-execution-agent.yaml`
- Modify: `infra/k8s/base/kustomization.yaml`

- [ ] **Step 1: Create agents kustomization**

Create `infra/k8s/base/agents/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - orchestrator.yaml
  - market-data-agent.yaml
  - portfolio-agent.yaml
  - news-sentiment-agent.yaml
  - trade-execution-agent.yaml
```

- [ ] **Step 2: Create orchestrator.yaml**

Create `infra/k8s/base/agents/orchestrator.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finflow-orchestrator
  namespace: finflow
  labels:
    app: finflow-orchestrator
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: finflow-orchestrator
  template:
    metadata:
      labels:
        app: finflow-orchestrator
    spec:
      containers:
        - name: agent
          image: finflow/orchestrator:latest
          ports:
            - containerPort: 8000
          env:
            - name: MARKET_DATA_AGENT_URL
              value: "http://market-data-agent:8000"
            - name: PORTFOLIO_AGENT_URL
              value: "http://portfolio-agent:8000"
            - name: NEWS_SENTIMENT_AGENT_URL
              value: "http://news-sentiment-agent:8000"
            - name: TRADE_EXECUTION_AGENT_URL
              value: "http://trade-execution-agent:8000"
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: finflow-orchestrator
  namespace: finflow
  labels:
    app: finflow-orchestrator
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: finflow-orchestrator
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 3: Create market-data-agent.yaml**

Create `infra/k8s/base/agents/market-data-agent.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: market-data-agent
  namespace: finflow
  labels:
    app: market-data-agent
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: market-data-agent
  template:
    metadata:
      labels:
        app: market-data-agent
    spec:
      containers:
        - name: agent
          image: finflow/market-data-agent:latest
          ports:
            - containerPort: 8000
          env:
            - name: MARKET_DATA_MCP_URL
              value: "http://agentgateway.finflow.svc/mcp/market-data/mcp/"
            - name: LLM_BASE_URL
              value: "http://agentgateway.finflow.svc/v1"
            - name: LLM_MODEL
              value: "openai/gpt-4o"
            - name: LLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: finflow-llm
                  key: api-key
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 20
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: market-data-agent
  namespace: finflow
  labels:
    app: market-data-agent
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: market-data-agent
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 4: Create portfolio-agent.yaml**

Create `infra/k8s/base/agents/portfolio-agent.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: portfolio-agent
  namespace: finflow
  labels:
    app: portfolio-agent
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: portfolio-agent
  template:
    metadata:
      labels:
        app: portfolio-agent
    spec:
      containers:
        - name: agent
          image: finflow/portfolio-agent:latest
          ports:
            - containerPort: 8000
          env:
            - name: PORTFOLIO_MCP_URL
              value: "http://agentgateway.finflow.svc/mcp/portfolio/mcp/"
            - name: LLM_BASE_URL
              value: "http://agentgateway.finflow.svc/v1"
            - name: LLM_MODEL
              value: "openai/gpt-4o"
            - name: LLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: finflow-llm
                  key: api-key
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 20
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: portfolio-agent
  namespace: finflow
  labels:
    app: portfolio-agent
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: portfolio-agent
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 5: Create news-sentiment-agent.yaml**

Create `infra/k8s/base/agents/news-sentiment-agent.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: news-sentiment-agent
  namespace: finflow
  labels:
    app: news-sentiment-agent
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: news-sentiment-agent
  template:
    metadata:
      labels:
        app: news-sentiment-agent
    spec:
      containers:
        - name: agent
          image: finflow/news-sentiment-agent:latest
          ports:
            - containerPort: 8000
          env:
            - name: NEWS_MCP_URL
              value: "http://agentgateway.finflow.svc/mcp/news/mcp/"
            - name: ANTHROPIC_BASE_URL
              value: "http://agentgateway.finflow.svc"
            - name: LLM_MODEL
              value: "claude-opus-4-6"
            - name: LLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: finflow-llm
                  key: api-key
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 20
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: news-sentiment-agent
  namespace: finflow
  labels:
    app: news-sentiment-agent
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: news-sentiment-agent
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 6: Create trade-execution-agent.yaml**

Create `infra/k8s/base/agents/trade-execution-agent.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trade-execution-agent
  namespace: finflow
  labels:
    app: trade-execution-agent
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: trade-execution-agent
  template:
    metadata:
      labels:
        app: trade-execution-agent
    spec:
      containers:
        - name: agent
          image: finflow/trade-execution-agent:latest
          ports:
            - containerPort: 8000
          env:
            - name: BROKERAGE_MCP_URL
              value: "http://agentgateway.finflow.svc/mcp/brokerage/mcp/"
            - name: ANTHROPIC_BASE_URL
              value: "http://agentgateway.finflow.svc"
            - name: LLM_MODEL
              value: "claude-opus-4-6"
            - name: LLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: finflow-llm
                  key: api-key
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 20
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: trade-execution-agent
  namespace: finflow
  labels:
    app: trade-execution-agent
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: trade-execution-agent
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 7: Update base kustomization to include agents**

Edit `infra/k8s/base/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - mcp-servers/
  - agents/
```

- [ ] **Step 8: Validate all YAML**

```bash
python3 -c "
import yaml, glob, sys
files = glob.glob('infra/k8s/base/agents/*.yaml')
errors = []
for f in files:
    try:
        list(yaml.safe_load_all(open(f)))
        print(f'OK: {f}')
    except yaml.YAMLError as e:
        errors.append(f'{f}: {e}')
for e in errors:
    print(f'ERROR: {e}', file=sys.stderr)
sys.exit(len(errors))
"
```

Expected: 6 lines of `OK: infra/k8s/base/agents/....yaml`

- [ ] **Step 9: Commit**

```bash
git add infra/k8s/base/agents/ infra/k8s/base/kustomization.yaml
git commit -m "chore: add K8s manifests for all 5 agents"
```

---

## Task 7: Makefile and kustomization updates

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Update Makefile**

Replace the entire `Makefile` with:

```makefile
REGISTRY ?= localhost:5000
TAG ?= latest

.PHONY: test-mcp test-agents test-all build push

# ── MCP server tests ─────────────────────────────────────────────────────────────
test-market-data:
	cd mcp-servers/market-data-mcp && uv run pytest tests/ -v

test-portfolio:
	cd mcp-servers/portfolio-mcp && uv run pytest tests/ -v

test-news:
	cd mcp-servers/news-mcp && uv run pytest tests/ -v

test-brokerage:
	cd mcp-servers/brokerage-mcp && uv run pytest tests/ -v

test-mcp: test-market-data test-portfolio test-news test-brokerage

# ── Agent tests ──────────────────────────────────────────────────────────────────
test-orchestrator:
	cd agents/orchestrator && uv run pytest tests/ -v

test-market-data-agent:
	cd agents/market-data && uv run pytest tests/ -v

test-portfolio-agent:
	cd agents/portfolio && uv run pytest tests/ -v

test-news-sentiment-agent:
	cd agents/news-sentiment && uv run pytest tests/ -v

test-trade-execution-agent:
	cd agents/trade-execution && uv run pytest tests/ -v

test-agents: test-orchestrator test-market-data-agent test-portfolio-agent test-news-sentiment-agent test-trade-execution-agent

# ── All tests ────────────────────────────────────────────────────────────────────
test-all: test-mcp test-agents

# ── Docker build ─────────────────────────────────────────────────────────────────
build:
	docker build -t $(REGISTRY)/finflow/market-data-mcp:$(TAG) mcp-servers/market-data-mcp
	docker build -t $(REGISTRY)/finflow/portfolio-mcp:$(TAG) mcp-servers/portfolio-mcp
	docker build -t $(REGISTRY)/finflow/news-mcp:$(TAG) mcp-servers/news-mcp
	docker build -t $(REGISTRY)/finflow/brokerage-mcp:$(TAG) mcp-servers/brokerage-mcp
	docker build -t $(REGISTRY)/finflow/orchestrator:$(TAG) agents/orchestrator
	docker build -t $(REGISTRY)/finflow/market-data-agent:$(TAG) agents/market-data
	docker build -t $(REGISTRY)/finflow/portfolio-agent:$(TAG) agents/portfolio
	docker build -t $(REGISTRY)/finflow/news-sentiment-agent:$(TAG) agents/news-sentiment
	docker build -t $(REGISTRY)/finflow/trade-execution-agent:$(TAG) agents/trade-execution

# ── Docker push ──────────────────────────────────────────────────────────────────
push:
	docker push $(REGISTRY)/finflow/market-data-mcp:$(TAG)
	docker push $(REGISTRY)/finflow/portfolio-mcp:$(TAG)
	docker push $(REGISTRY)/finflow/news-mcp:$(TAG)
	docker push $(REGISTRY)/finflow/brokerage-mcp:$(TAG)
	docker push $(REGISTRY)/finflow/orchestrator:$(TAG)
	docker push $(REGISTRY)/finflow/market-data-agent:$(TAG)
	docker push $(REGISTRY)/finflow/portfolio-agent:$(TAG)
	docker push $(REGISTRY)/finflow/news-sentiment-agent:$(TAG)
	docker push $(REGISTRY)/finflow/trade-execution-agent:$(TAG)
```

- [ ] **Step 2: Run test-agents to verify all agent tests pass**

```bash
make test-agents
```

Expected: all 5 agent test suites pass (orchestrator: 8, market-data: 7, portfolio: 5, news-sentiment: 6, trade-execution: 6 = 32 tests total).

- [ ] **Step 3: Run test-all to verify everything passes**

```bash
make test-all
```

Expected: all 57 tests pass (25 MCP + 32 agents).

- [ ] **Step 4: Commit**

```bash
git add Makefile
git commit -m "chore: extend Makefile with agent test/build/push targets"
```
