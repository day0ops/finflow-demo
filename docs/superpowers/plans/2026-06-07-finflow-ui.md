# FinFlow UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-page FinFlow demo UI — a Python FastAPI BFF plus a Next.js frontend with chat panel, data panel, left policies drawer, and bottom trace overlay — wired to the existing orchestrator.

**Architecture:** A new `bff/` FastAPI service sits between the Next.js `ui/` and the existing orchestrator (port 8000). The BFF adds policy enforcement (RBAC, elicitation, guardrails, rate limit demo events), collects BFF-side trace metadata (intent, agents, latency, policy events), and serves portfolio/ticker data from `infra/mock-data/`. The UI is a single App Router page: Nav + Chat (left, full height) + Data (right, full height) + Policies drawer (left slide-in, absolute) + Trace panel (bottom overlay, absolute).

**Tech Stack:** Python 3.12, FastAPI, httpx, uvicorn, sqlite3 (BFF) · Next.js 15 App Router, TypeScript, CSS Variables/globals.css (UI) · pytest + respx (BFF tests) · Jest + @testing-library/react (UI tests)

---

## File Map

### BFF (`bff/`)

| Path | Role |
|---|---|
| `bff/pyproject.toml` | Dependencies + pytest config |
| `bff/main.py` | FastAPI app + CORS + router wiring |
| `bff/models.py` | All Pydantic request/response models |
| `bff/mock.py` | Load tickers.json + holdings.sql into memory |
| `bff/trace.py` | TraceCapture helper (builds TraceData) |
| `bff/routes/health.py` | GET /api/health |
| `bff/routes/tickers.py` | GET /api/tickers |
| `bff/routes/portfolio.py` | GET /api/portfolio |
| `bff/routes/policies.py` | GET/POST /api/policies (in-memory state) |
| `bff/routes/chat.py` | POST /api/chat (policy checks + orchestrator proxy) |
| `bff/tests/test_health.py` | Health endpoint tests |
| `bff/tests/test_mock.py` | Mock data loader tests |
| `bff/tests/test_tickers.py` | Tickers endpoint tests |
| `bff/tests/test_portfolio.py` | Portfolio endpoint tests |
| `bff/tests/test_policies.py` | Policy state tests |
| `bff/tests/test_chat.py` | Chat endpoint tests (RBAC, elicitation, guardrails, proxy) |
| `bff/Dockerfile` | BFF container |

### UI (`ui/`)

| Path | Role |
|---|---|
| `ui/package.json` | Dependencies |
| `ui/tsconfig.json` | TypeScript config |
| `ui/next.config.ts` | API rewrites (proxy `/api/*` → BFF in dev) |
| `ui/jest.config.ts` | Jest config |
| `ui/jest.setup.ts` | @testing-library/jest-dom setup |
| `ui/src/app/globals.css` | CSS variables (design tokens) + all component styles |
| `ui/src/app/layout.tsx` | Root layout (font, bg, viewport) |
| `ui/src/app/page.tsx` | Single page — wires all panels |
| `ui/src/lib/types.ts` | Shared TypeScript interfaces |
| `ui/src/lib/api.ts` | fetch wrappers for BFF endpoints |
| `ui/src/components/NavBar.tsx` | Nav: Policies button + wordmark + status dot |
| `ui/src/components/ChatBubble.tsx` | User/AI chat bubble with agent meta line |
| `ui/src/components/ChatInput.tsx` | Textarea + Send button |
| `ui/src/components/ChatPanel.tsx` | Message list + input area |
| `ui/src/components/TickerCard.tsx` | Single market data cell |
| `ui/src/components/PortfolioCard.tsx` | Holdings list + total value |
| `ui/src/components/DataPanel.tsx` | Right column (tickers grid + portfolio) |
| `ui/src/components/PolicyRow.tsx` | Single policy toggle row |
| `ui/src/components/PolicyDrawer.tsx` | Left sliding drawer with 4 policy rows |
| `ui/src/components/TracePanel.tsx` | Bottom expandable overlay |
| `ui/src/hooks/useChat.ts` | Chat state: messages, send, elicitation flow |
| `ui/src/hooks/usePolicies.ts` | Policy state: fetch on mount, toggle calls POST |
| `ui/src/hooks/usePortfolio.ts` | Portfolio fetch (refresh every 30s) |
| `ui/src/hooks/useTickers.ts` | Tickers fetch (refresh every 10s) |
| `ui/src/__tests__/NavBar.test.tsx` | NavBar render test |
| `ui/src/__tests__/ChatBubble.test.tsx` | Bubble variants test |
| `ui/src/__tests__/ChatInput.test.tsx` | Input submit test |
| `ui/src/__tests__/PolicyDrawer.test.tsx` | Drawer open/close + toggle test |
| `ui/src/__tests__/TracePanel.test.tsx` | Expand/collapse test |
| `ui/src/__tests__/useChat.test.ts` | Chat hook: send + RBAC block + elicitation |
| `ui/src/__tests__/usePolicies.test.ts` | Policy hook: fetch + toggle |
| `ui/Dockerfile` | UI container |

---

## Phase 1: BFF

### Task 1: BFF scaffold + health endpoint

**Files:**
- Create: `bff/pyproject.toml`
- Create: `bff/main.py`
- Create: `bff/routes/__init__.py`
- Create: `bff/routes/health.py`
- Create: `bff/tests/__init__.py`
- Create: `bff/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

```python
# bff/tests/test_health.py
from fastapi.testclient import TestClient

def test_health_returns_status_ok():
    from main import app
    with TestClient(app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "orchestrator" in data
    assert isinstance(data["orchestrator"], bool)
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd bff && uv run pytest tests/test_health.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Create `bff/pyproject.toml`**

```toml
[project]
name = "finflow-bff"
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
    "httpx>=0.27.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 4: Install dependencies**

```bash
cd bff && uv sync
```

Expected: lockfile created, deps installed.

- [ ] **Step 5: Create `bff/routes/health.py`**

```python
import os
import httpx
from fastapi import APIRouter

router = APIRouter()

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

@router.get("/api/health")
async def health():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ORCHESTRATOR_URL}/health", timeout=2.0)
        orchestrator_ok = resp.status_code == 200
    except Exception:
        orchestrator_ok = False
    return {"status": "ok", "orchestrator": orchestrator_ok}
```

- [ ] **Step 6: Create `bff/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health import router as health_router

app = FastAPI(title="finflow-bff")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
```

- [ ] **Step 7: Create empty `__init__.py` files**

```bash
touch bff/routes/__init__.py bff/tests/__init__.py
```

- [ ] **Step 8: Run test — verify it passes**

```bash
cd bff && uv run pytest tests/test_health.py -v
```

Expected: `PASSED`

- [ ] **Step 9: Commit**

```bash
git add bff/
git commit -m "feat(bff): scaffold BFF with health endpoint"
```

---

### Task 2: Pydantic models + mock data loader

**Files:**
- Create: `bff/models.py`
- Create: `bff/mock.py`
- Create: `bff/tests/test_mock.py`

- [ ] **Step 1: Write the failing test**

```python
# bff/tests/test_mock.py
def test_load_tickers_has_expected_symbols():
    from mock import load_tickers
    data = load_tickers()
    assert "NVDA" in data
    assert "AAPL" in data
    assert "MSFT" in data
    assert data["NVDA"]["price"] > 0
    assert isinstance(data["NVDA"]["change_pct"], float)

def test_load_holdings_morgan_has_four_rows():
    from mock import get_holdings_conn
    conn = get_holdings_conn()
    rows = conn.execute(
        "SELECT ticker FROM holdings WHERE user_id='morgan'"
    ).fetchall()
    assert len(rows) == 4
    tickers = {r[0] for r in rows}
    assert "NVDA" in tickers
    assert "AAPL" in tickers

def test_singleton_tickers_returns_same_object():
    from mock import tickers
    a = tickers()
    b = tickers()
    assert a is b

def test_singleton_db_returns_same_connection():
    from mock import db
    a = db()
    b = db()
    assert a is b
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd bff && uv run pytest tests/test_mock.py -v
```

Expected: `ModuleNotFoundError: No module named 'mock'`

- [ ] **Step 3: Create `bff/models.py`**

```python
from pydantic import BaseModel

class TickerOut(BaseModel):
    ticker: str
    name: str
    price: float
    change_pct: float
    volume: int

class TickersResponse(BaseModel):
    tickers: list[TickerOut]

class HoldingOut(BaseModel):
    ticker: str
    name: str
    shares: float
    cost_basis: float
    current_price: float
    market_value: float
    pnl_pct: float

class PortfolioResponse(BaseModel):
    holdings: list[HoldingOut]
    total_value: float

class PolicyState(BaseModel):
    rbac: bool = False
    elicitation: bool = False
    rate_limit: bool = False
    guardrails: bool = False

class PolicyUpdate(BaseModel):
    rbac: bool | None = None
    elicitation: bool | None = None
    rate_limit: bool | None = None
    guardrails: bool | None = None

class PolicyEvent(BaseModel):
    type: str
    policy: str
    verdict: str
    message: str

class TraceData(BaseModel):
    intent: str
    agents: list[str]
    latency_ms: int
    status_code: int
    policy_events: list[PolicyEvent]

class ElicitationData(BaseModel):
    required: bool = True
    prompt: str
    trade_details: str

class ChatRequest(BaseModel):
    message: str
    session_id: str
    confirmed: bool = False

class ChatResponse(BaseModel):
    message: str
    trace: TraceData
    elicitation: ElicitationData | None = None
```

- [ ] **Step 4: Create `bff/mock.py`**

```python
import json
import sqlite3
from pathlib import Path

_MOCK_DIR = Path(__file__).parent.parent / "infra" / "mock-data"

def load_tickers() -> dict:
    with open(_MOCK_DIR / "tickers.json") as f:
        return json.load(f)

def get_holdings_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    sql = (_MOCK_DIR / "holdings.sql").read_text()
    conn.executescript(sql)
    conn.commit()
    return conn

_tickers: dict | None = None
_conn: sqlite3.Connection | None = None

def tickers() -> dict:
    global _tickers
    if _tickers is None:
        _tickers = load_tickers()
    return _tickers

def db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = get_holdings_conn()
    return _conn
```

- [ ] **Step 5: Run test — verify it passes**

```bash
cd bff && uv run pytest tests/test_mock.py -v
```

Expected: all 4 tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add bff/models.py bff/mock.py bff/tests/test_mock.py
git commit -m "feat(bff): add Pydantic models and mock data loader"
```

---

### Task 3: GET /api/tickers and GET /api/portfolio

**Files:**
- Create: `bff/routes/tickers.py`
- Create: `bff/routes/portfolio.py`
- Create: `bff/tests/test_tickers.py`
- Create: `bff/tests/test_portfolio.py`
- Modify: `bff/main.py`

- [ ] **Step 1: Write the failing tests**

```python
# bff/tests/test_tickers.py
from fastapi.testclient import TestClient

def test_get_tickers_returns_all_symbols():
    from main import app
    with TestClient(app) as client:
        resp = client.get("/api/tickers")
    assert resp.status_code == 200
    data = resp.json()
    assert "tickers" in data
    symbols = {t["ticker"] for t in data["tickers"]}
    assert symbols >= {"NVDA", "AAPL", "MSFT", "GOOGL", "AMZN"}

def test_get_tickers_shape():
    from main import app
    with TestClient(app) as client:
        resp = client.get("/api/tickers")
    first = resp.json()["tickers"][0]
    assert "ticker" in first
    assert "name" in first
    assert "price" in first
    assert "change_pct" in first
    assert "volume" in first
```

```python
# bff/tests/test_portfolio.py
from fastapi.testclient import TestClient

def test_get_portfolio_has_holdings():
    from main import app
    with TestClient(app) as client:
        resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    data = resp.json()
    assert "holdings" in data
    assert "total_value" in data
    assert data["total_value"] > 0
    symbols = {h["ticker"] for h in data["holdings"]}
    assert "NVDA" in symbols

def test_get_portfolio_holding_shape():
    from main import app
    with TestClient(app) as client:
        resp = client.get("/api/portfolio")
    h = resp.json()["holdings"][0]
    for field in ("ticker", "name", "shares", "cost_basis", "current_price", "market_value", "pnl_pct"):
        assert field in h

def test_get_portfolio_total_value_equals_sum_of_market_values():
    from main import app
    with TestClient(app) as client:
        resp = client.get("/api/portfolio")
    data = resp.json()
    expected = round(sum(h["market_value"] for h in data["holdings"]), 2)
    assert abs(data["total_value"] - expected) < 0.01
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd bff && uv run pytest tests/test_tickers.py tests/test_portfolio.py -v
```

Expected: `404 Not Found` (routes not registered yet)

- [ ] **Step 3: Create `bff/routes/tickers.py`**

```python
from fastapi import APIRouter
from models import TickersResponse, TickerOut
import mock as mock_data

router = APIRouter()

@router.get("/api/tickers", response_model=TickersResponse)
def get_tickers():
    data = mock_data.tickers()
    return TickersResponse(tickers=[
        TickerOut(
            ticker=v["ticker"],
            name=v["name"],
            price=v["price"],
            change_pct=v["change_pct"],
            volume=v["volume"],
        )
        for v in data.values()
    ])
```

- [ ] **Step 4: Create `bff/routes/portfolio.py`**

```python
from fastapi import APIRouter
from models import PortfolioResponse, HoldingOut
import mock as mock_data

router = APIRouter()

_USER_ID = "morgan"

@router.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio():
    price_map = mock_data.tickers()
    rows = mock_data.db().execute(
        "SELECT ticker, shares, cost_basis FROM holdings WHERE user_id=?",
        (_USER_ID,),
    ).fetchall()
    holdings: list[HoldingOut] = []
    total = 0.0
    for ticker, shares, cost_basis in rows:
        if ticker not in price_map:
            continue
        current = price_map[ticker]["price"]
        market_value = round(shares * current, 2)
        pnl_pct = round((current - cost_basis) / cost_basis * 100, 2)
        total += market_value
        holdings.append(HoldingOut(
            ticker=ticker,
            name=price_map[ticker]["name"],
            shares=shares,
            cost_basis=cost_basis,
            current_price=current,
            market_value=market_value,
            pnl_pct=pnl_pct,
        ))
    return PortfolioResponse(holdings=holdings, total_value=round(total, 2))
```

- [ ] **Step 5: Register routes in `bff/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health import router as health_router
from routes.tickers import router as tickers_router
from routes.portfolio import router as portfolio_router

app = FastAPI(title="finflow-bff")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(tickers_router)
app.include_router(portfolio_router)
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
cd bff && uv run pytest tests/test_tickers.py tests/test_portfolio.py -v
```

Expected: all 5 tests `PASSED`

- [ ] **Step 7: Commit**

```bash
git add bff/routes/tickers.py bff/routes/portfolio.py bff/tests/test_tickers.py bff/tests/test_portfolio.py bff/main.py
git commit -m "feat(bff): add /api/tickers and /api/portfolio endpoints"
```

---

### Task 4: GET/POST /api/policies

**Files:**
- Create: `bff/routes/policies.py`
- Create: `bff/tests/test_policies.py`
- Modify: `bff/main.py`

- [ ] **Step 1: Write the failing tests**

```python
# bff/tests/test_policies.py
from fastapi.testclient import TestClient

def _reset(client: TestClient):
    client.post("/api/policies", json={
        "rbac": False, "elicitation": False,
        "rate_limit": False, "guardrails": False
    })

def test_get_policies_default_all_false():
    from main import app
    with TestClient(app) as client:
        _reset(client)
        resp = client.get("/api/policies")
    assert resp.status_code == 200
    assert resp.json() == {
        "rbac": False, "elicitation": False,
        "rate_limit": False, "guardrails": False,
    }

def test_post_policies_enables_rbac():
    from main import app
    with TestClient(app) as client:
        _reset(client)
        resp = client.post("/api/policies", json={"rbac": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["rbac"] is True
    assert data["elicitation"] is False

def test_post_policies_partial_update_preserves_other_fields():
    from main import app
    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"elicitation": True})
        resp = client.post("/api/policies", json={"rbac": True})
    data = resp.json()
    assert data["rbac"] is True
    assert data["elicitation"] is True
    assert data["rate_limit"] is False
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd bff && uv run pytest tests/test_policies.py -v
```

Expected: `404 Not Found`

- [ ] **Step 3: Create `bff/routes/policies.py`**

```python
from fastapi import APIRouter
from models import PolicyState, PolicyUpdate

router = APIRouter()

# In-memory demo state — single shared instance per process
_state = PolicyState()

@router.get("/api/policies", response_model=PolicyState)
def get_policies():
    return _state

@router.post("/api/policies", response_model=PolicyState)
def update_policies(update: PolicyUpdate):
    if update.rbac is not None:
        _state.rbac = update.rbac
    if update.elicitation is not None:
        _state.elicitation = update.elicitation
    if update.rate_limit is not None:
        _state.rate_limit = update.rate_limit
    if update.guardrails is not None:
        _state.guardrails = update.guardrails
    return _state
```

- [ ] **Step 4: Register route in `bff/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health import router as health_router
from routes.tickers import router as tickers_router
from routes.portfolio import router as portfolio_router
from routes.policies import router as policies_router

app = FastAPI(title="finflow-bff")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(tickers_router)
app.include_router(portfolio_router)
app.include_router(policies_router)
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd bff && uv run pytest tests/test_policies.py -v
```

Expected: all 3 tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add bff/routes/policies.py bff/tests/test_policies.py bff/main.py
git commit -m "feat(bff): add /api/policies state management"
```

---

### Task 5: TraceCapture + POST /api/chat

**Files:**
- Create: `bff/trace.py`
- Create: `bff/routes/chat.py`
- Create: `bff/tests/test_chat.py`
- Modify: `bff/main.py`

- [ ] **Step 1: Write the failing tests**

```python
# bff/tests/test_chat.py
import pytest
import respx
import httpx
from fastapi.testclient import TestClient

def _reset(client: TestClient):
    client.post("/api/policies", json={
        "rbac": False, "elicitation": False,
        "rate_limit": False, "guardrails": False,
    })

@respx.mock
def test_chat_briefing_proxies_to_orchestrator():
    respx.post("http://localhost:8000/run").mock(
        return_value=httpx.Response(200, json={
            "output": "Portfolio briefing: NVDA up 2.4%",
            "session_id": "s1",
            "agent": "finflow-orchestrator",
        })
    )
    from main import app
    with TestClient(app) as client:
        _reset(client)
        resp = client.post("/api/chat", json={"message": "show my portfolio", "session_id": "s1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Portfolio briefing" in data["message"]
    assert data["trace"]["intent"] == "briefing"
    assert "portfolio-agent" in data["trace"]["agents"]
    assert data["elicitation"] is None

@respx.mock
def test_chat_rbac_blocks_trade_without_proxy():
    from main import app
    # No mock needed — RBAC should block before calling orchestrator
    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"rbac": True})
        resp = client.post("/api/chat", json={"message": "buy 10 shares of NVDA", "session_id": "s1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "denied" in data["message"].lower()
    assert data["trace"]["status_code"] == 403
    assert data["trace"]["policy_events"][0]["type"] == "rbac_block"
    assert data["trace"]["policy_events"][0]["verdict"] == "deny"
    assert data["elicitation"] is None

def test_chat_elicitation_gates_unconfirmed_trade():
    from main import app
    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"elicitation": True})
        resp = client.post("/api/chat", json={"message": "buy 10 shares of NVDA", "session_id": "s1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["elicitation"] is not None
    assert data["elicitation"]["required"] is True
    assert data["trace"]["policy_events"][0]["type"] == "elicitation_required"

@respx.mock
def test_chat_elicitation_confirmed_proxies():
    respx.post("http://localhost:8000/run").mock(
        return_value=httpx.Response(200, json={
            "output": "Trade executed: BUY 10 NVDA",
            "session_id": "s1",
            "agent": "finflow-orchestrator",
        })
    )
    from main import app
    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"elicitation": True})
        resp = client.post("/api/chat", json={
            "message": "buy 10 shares of NVDA",
            "session_id": "s1",
            "confirmed": True,
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "Trade executed" in data["message"]
    assert data["elicitation"] is None

def test_chat_guardrail_blocks_advice_language():
    from main import app
    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"guardrails": True})
        resp = client.post("/api/chat", json={
            "message": "give me a guaranteed profit trade",
            "session_id": "s1",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace"]["policy_events"][0]["type"] == "guardrail"
    assert data["trace"]["policy_events"][0]["verdict"] == "deny"
    assert data["trace"]["status_code"] == 400

def test_chat_rate_limit_adds_allow_event():
    from main import app
    with TestClient(app) as client:
        _reset(client)
        client.post("/api/policies", json={"rate_limit": True, "elicitation": True})
        resp = client.post("/api/chat", json={"message": "buy 5 AAPL", "session_id": "s1"})
    data = resp.json()
    types = [e["type"] for e in data["trace"]["policy_events"]]
    assert "rate_limit" in types
    rate_evt = next(e for e in data["trace"]["policy_events"] if e["type"] == "rate_limit")
    assert rate_evt["verdict"] == "allow"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd bff && uv run pytest tests/test_chat.py -v
```

Expected: `404 Not Found` (route not registered)

- [ ] **Step 3: Create `bff/trace.py`**

```python
import time
from models import TraceData, PolicyEvent

class TraceCapture:
    def __init__(self, intent: str):
        self.intent = intent
        self.agents: list[str] = []
        self.policy_events: list[PolicyEvent] = []
        self.status_code = 200
        self._start = time.monotonic()

    def add_agent(self, name: str) -> None:
        self.agents.append(name)

    def add_policy_event(self, event: PolicyEvent) -> None:
        self.policy_events.append(event)

    def build(self) -> TraceData:
        elapsed = int((time.monotonic() - self._start) * 1000)
        return TraceData(
            intent=self.intent,
            agents=self.agents,
            latency_ms=elapsed,
            status_code=self.status_code,
            policy_events=self.policy_events,
        )
```

- [ ] **Step 4: Create `bff/routes/chat.py`**

```python
import os
import httpx
from fastapi import APIRouter
from models import ChatRequest, ChatResponse, ElicitationData, PolicyEvent
from trace import TraceCapture
from routes.policies import _state as policy_state

router = APIRouter()

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

_TRADE_KEYWORDS = {"trade", "buy", "sell", "execute", "purchase", "shares"}
_BRIEFING_KEYWORDS = {
    "portfolio", "briefing", "holdings", "performance",
    "overview", "picture", "context", "news",
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
async def chat(req: ChatRequest):
    intent = _detect_intent(req.message)
    tc = TraceCapture(intent)

    # Guardrails
    if policy_state.guardrails:
        msg_lower = req.message.lower()
        if any(phrase in msg_lower for phrase in _GUARDRAIL_PHRASES):
            tc.add_policy_event(PolicyEvent(
                type="guardrail",
                policy="Guardrails",
                verdict="deny",
                message="Message contains prohibited financial advice language",
            ))
            tc.status_code = 400
            return ChatResponse(
                message="Request blocked. This message contains prohibited financial advice language (guaranteed returns, risk-free claims).",
                trace=tc.build(),
            )
        tc.add_policy_event(PolicyEvent(
            type="guardrail",
            policy="Guardrails",
            verdict="allow",
            message="No prohibited content detected",
        ))

    # Rate limit (demo: always allow, visible in trace)
    if policy_state.rate_limit:
        tc.add_policy_event(PolicyEvent(
            type="rate_limit",
            policy="Rate Limits",
            verdict="allow",
            message="10 req/min — budget ok (1/10 used)",
        ))

    # RBAC — block trade intent
    if policy_state.rbac and intent == "trade":
        tc.add_policy_event(PolicyEvent(
            type="rbac_block",
            policy="MCP RBAC",
            verdict="deny",
            message="TRADE agent requires 'trade' role — current role: viewer",
        ))
        tc.status_code = 403
        return ChatResponse(
            message="Request denied. Your role does not have TRADE permissions. Contact your administrator.",
            trace=tc.build(),
        )

    # Elicitation gate — unconfirmed trade
    if policy_state.elicitation and intent == "trade" and not req.confirmed:
        tc.add_policy_event(PolicyEvent(
            type="elicitation_required",
            policy="Elicitation",
            verdict="allow",
            message="Trade execution requires explicit user confirmation",
        ))
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
    except Exception:
        tc.status_code = 503
        return ChatResponse(
            message="Could not reach the orchestrator. Is it running?",
            trace=tc.build(),
        )

    return ChatResponse(message=output, trace=tc.build())
```

- [ ] **Step 5: Register route and add trace import to `bff/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health import router as health_router
from routes.tickers import router as tickers_router
from routes.portfolio import router as portfolio_router
from routes.policies import router as policies_router
from routes.chat import router as chat_router

app = FastAPI(title="finflow-bff")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(tickers_router)
app.include_router(portfolio_router)
app.include_router(policies_router)
app.include_router(chat_router)
```

- [ ] **Step 6: Run all BFF tests**

```bash
cd bff && uv run pytest tests/ -v
```

Expected: all tests `PASSED`

- [ ] **Step 7: Commit**

```bash
git add bff/trace.py bff/routes/chat.py bff/tests/test_chat.py bff/main.py
git commit -m "feat(bff): add trace capture and /api/chat with policy enforcement"
```

---

### Task 6: BFF Dockerfile

**Files:**
- Create: `bff/Dockerfile`

- [ ] **Step 1: Create `bff/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv sync --no-dev

COPY . .

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

- [ ] **Step 2: Add bff to Makefile**

In `Makefile`, add under `# ── MCP server tests`:

```makefile
test-bff:
	cd bff && uv run pytest tests/ -v

test-all: test-mcp test-agents test-bff
```

And under `# ── Docker build`:

```makefile
	docker build -t $(REGISTRY)/finflow/bff:$(TAG) bff
```

And under `# ── Docker push`:

```makefile
	docker push $(REGISTRY)/finflow/bff:$(TAG)
```

- [ ] **Step 3: Commit**

```bash
git add bff/Dockerfile Makefile
git commit -m "feat(bff): add Dockerfile and Makefile targets"
```

---

## Phase 2: UI (Next.js)

### Task 7: Next.js project scaffold

**Files:**
- Create: `ui/package.json`
- Create: `ui/tsconfig.json`
- Create: `ui/next.config.ts`
- Create: `ui/jest.config.ts`
- Create: `ui/jest.setup.ts`
- Create: `ui/src/app/globals.css`
- Create: `ui/src/app/layout.tsx`

- [ ] **Step 1: Create `ui/package.json`**

```json
{
  "name": "finflow-ui",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "jest --passWithNoTests"
  },
  "dependencies": {
    "next": "15.3.3",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.3.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/node": "^22",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "typescript": "^5"
  }
}
```

- [ ] **Step 2: Install dependencies**

```bash
cd ui && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 3: Create `ui/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 4: Create `ui/next.config.ts`**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8001/api/:path*",
      },
    ];
  },
};

export default nextConfig;
```

- [ ] **Step 5: Create `ui/jest.config.ts`**

```typescript
import type { Config } from "jest";
import nextJest from "next/jest.js";

const createJestConfig = nextJest({ dir: "./" });

const config: Config = {
  coverageProvider: "v8",
  testEnvironment: "jsdom",
  setupFilesAfterFramework: ["<rootDir>/jest.setup.ts"],
};

export default createJestConfig(config);
```

- [ ] **Step 6: Create `ui/jest.setup.ts`**

```typescript
import "@testing-library/jest-dom";
```

- [ ] **Step 7: Create directory structure**

```bash
mkdir -p ui/src/app ui/src/components ui/src/hooks ui/src/lib ui/src/__tests__
```

- [ ] **Step 8: Create `ui/src/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinFlow",
  description: "Multi-agent financial portfolio assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 9: Create `ui/src/app/globals.css`** (design tokens + full component styles)

```css
/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
button { font-family: inherit; cursor: pointer; }
input, textarea { font-family: inherit; }

/* ── Design tokens ── */
:root {
  --bg:    #090c12;
  --bg2:   #0d1220;
  --bg3:   #101828;
  --bd:    rgba(29,138,255,0.12);
  --blue:  #1d8aff;
  --blue-h:#3a9bff;
  --bdim:  rgba(29,138,255,0.08);
  --green: #00e07a;
  --red:   #ff4d6a;
  --amber: #f0a500;
  --text:  #dde4ed;
  --muted: rgba(221,228,237,0.42);
  --font:  -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --panel-w:         280px;
  --trace-collapsed: 36px;
  --trace-expanded:  260px;
  --ease:  cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Base ── */
html, body { height: 100%; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 13px;
  line-height: 1.5;
  overflow: hidden;
}

/* ── App shell ── */
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* ── Layout (below nav) ── */
.layout {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
  /* Bottom padding accounts for collapsed trace bar */
  padding-bottom: var(--trace-collapsed);
}

/* ── Content (chat + data) ── */
.content {
  flex: 1;
  display: flex;
  overflow: hidden;
  transition: margin-left 250ms var(--ease);
}
.content.pushed { margin-left: var(--panel-w); }

/* ── Nav ── */
.nav {
  height: 44px;
  background: var(--bg2);
  border-bottom: 1px solid var(--bd);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  flex-shrink: 0;
  z-index: 10;
}
.nav-left, .nav-right { display: flex; align-items: center; gap: 12px; }
.nav-policies-btn {
  background: var(--bg3);
  border: 1px solid var(--bd);
  border-radius: 7px;
  color: var(--text);
  font-size: 12px;
  font-weight: 500;
  padding: 5px 10px;
}
.nav-wordmark {
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--blue);
}
.nav-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse 2s ease-in-out infinite;
}
.nav-status-label { font-size: 11px; color: var(--muted); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* ── Chat panel ── */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--bd);
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chat-footer {
  padding: 9px 12px;
  background: var(--bg2);
  border-top: 1px solid var(--bd);
  display: flex;
  gap: 9px;
  align-items: flex-end;
}

/* ── Chat bubbles ── */
.bubble {
  max-width: 80%;
  font-size: 13px;
  line-height: 1.5;
  padding: 9px 12px;
  border-radius: 10px;
}
.bubble-user {
  align-self: flex-end;
  background: rgba(29,138,255,0.08);
  border: 1px solid rgba(29,138,255,0.18);
  border-radius: 10px 10px 2px 10px;
  color: #9ec8f8;
}
.bubble-ai {
  align-self: flex-start;
  background: rgba(29,138,255,0.06);
  border: 1px solid rgba(29,138,255,0.14);
  border-radius: 2px 10px 10px 10px;
  color: var(--text);
}
.bubble-blocked {
  border-color: rgba(255,77,106,0.25);
}
.bubble-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.bubble-agent { font-size: 10px; font-weight: 600; letter-spacing: 0.04em; color: var(--muted); }
.bubble-latency { font-size: 10px; color: rgba(221,228,237,0.3); margin-left: auto; }
.bubble-denied { color: var(--red); }
.bubble-muted { color: var(--muted); }

/* ── Agent tag ── */
.agent-tag {
  display: inline-block;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  background: rgba(29,138,255,0.12);
  border: 1px solid rgba(29,138,255,0.25);
  color: #6aaeff;
  border-radius: 3px;
  padding: 1px 5px;
}
.agent-tag-blocked {
  background: rgba(255,77,106,0.12);
  border-color: rgba(255,77,106,0.25);
  color: var(--red);
}
.agent-tag-policy {
  background: rgba(240,165,0,0.12);
  border-color: rgba(240,165,0,0.25);
  color: var(--amber);
}

/* ── Chat input ── */
.chat-input {
  flex: 1;
  background: var(--bg3);
  border: 1px solid var(--bd);
  border-radius: 7px;
  color: var(--text);
  font-size: 13px;
  padding: 8px 13px;
  resize: none;
  min-height: 38px;
  max-height: 120px;
  overflow-y: auto;
}
.chat-input::placeholder { color: var(--muted); }
.chat-input:focus { outline: none; border-color: rgba(29,138,255,0.3); }

/* ── Send button ── */
.btn-send {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 7px;
  background: var(--blue);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s var(--ease);
}
.btn-send:hover { background: var(--blue-h); }
.btn-send:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Confirm button ── */
.btn-confirm {
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 11px;
  font-weight: 600;
  margin-top: 10px;
  transition: background 0.2s var(--ease);
}
.btn-confirm:hover { background: var(--blue-h); }

/* ── Data panel ── */
.data-panel {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 12px;
  gap: 12px;
}

/* ── Section label ── */
.section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
}

/* ── Ticker grid ── */
.ticker-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
}
.ticker-card {
  background: var(--bg3);
  border: 1px solid var(--bd);
  border-radius: 7px;
  padding: 9px;
  text-align: center;
}
.ticker-symbol {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--blue);
  margin-bottom: 4px;
}
.ticker-price {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 2px;
}
.ticker-change { font-size: 10px; }
.ticker-change.pos { color: var(--green); }
.ticker-change.neg { color: var(--red); }

/* ── Portfolio card ── */
.portfolio-card {
  background: var(--bg3);
  border: 1px solid var(--bd);
  border-radius: 7px;
  padding: 12px;
}
.portfolio-value {
  font-size: 20px;
  font-weight: 800;
  line-height: 1.1;
  color: var(--text);
  margin-bottom: 12px;
}
.portfolio-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-top: 1px solid rgba(29,138,255,0.06);
  font-size: 12px;
}
.portfolio-ticker { font-weight: 600; color: var(--blue); }
.portfolio-shares { color: var(--muted); font-size: 11px; }
.portfolio-value-cell { font-weight: 600; }
.portfolio-pnl.pos { color: var(--green); font-size: 11px; }
.portfolio-pnl.neg { color: var(--red); font-size: 11px; }

/* ── Policy drawer ── */
.drawer {
  position: absolute;
  top: 0; left: 0; bottom: 0;
  width: var(--panel-w);
  background: var(--bg2);
  border-right: 1px solid var(--bd);
  box-shadow: 4px 0 28px rgba(0,0,0,0.5);
  transform: translateX(-100%);
  transition: transform 250ms var(--ease);
  z-index: 20;
  display: flex;
  flex-direction: column;
}
.drawer.open { transform: translateX(0); }
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--bd);
  flex-shrink: 0;
}
.drawer-title {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
.drawer-close {
  background: none;
  border: none;
  color: var(--muted);
  font-size: 18px;
  line-height: 1;
  padding: 2px;
}
.drawer-body { flex: 1; overflow-y: auto; padding: 9px; display: flex; flex-direction: column; gap: 6px; }

/* ── Policy row ── */
.policy-row {
  background: var(--bg3);
  border: 1px solid var(--bd);
  border-radius: 7px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.policy-info { flex: 1; }
.policy-name { font-size: 12px; font-weight: 500; color: var(--text); margin-bottom: 2px; }
.policy-desc { font-size: 11px; color: var(--muted); }

/* ── Toggle ── */
.toggle { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; flex-shrink: 0; }
.toggle input { position: absolute; opacity: 0; width: 0; height: 0; }
.toggle-track {
  position: relative;
  width: 34px; height: 19px;
  border-radius: 20px;
  background: rgba(255,255,255,0.10);
  transition: background 0.2s var(--ease);
  flex-shrink: 0;
}
.toggle-knob {
  position: absolute;
  top: 2px; left: 2px;
  width: 15px; height: 15px;
  border-radius: 50%;
  background: rgba(255,255,255,0.6);
  transition: left 0.2s var(--ease), background 0.2s var(--ease);
}
.toggle input:checked ~ .toggle-track { background: var(--blue); }
.toggle input:checked ~ .toggle-track .toggle-knob { left: 17px; background: #fff; }

/* ── Trace panel ── */
.trace-panel {
  position: absolute;
  left: 0; right: 0; bottom: 0;
  z-index: 12;
  background: var(--bg2);
  border-top: 1px solid var(--bd);
  box-shadow: 0 -4px 24px rgba(0,0,0,0.5);
  height: var(--trace-collapsed);
  transition: height 280ms var(--ease);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.trace-panel.open { height: var(--trace-expanded); }
.trace-bar {
  height: var(--trace-collapsed);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  cursor: pointer;
  flex-shrink: 0;
  user-select: none;
}
.trace-summary { font-size: 11px; color: var(--muted); }
.trace-chevron {
  font-size: 9px;
  color: var(--muted);
  transition: transform 280ms var(--ease);
}
.trace-panel.open .trace-chevron { transform: rotate(180deg); }
.trace-body {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  overflow-y: auto;
  padding: 9px;
  border-top: 1px solid var(--bd);
}
.trace-col-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 6px;
}
.trace-event {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 4px 0;
  font-size: 11px;
  color: var(--muted);
  border-bottom: 1px solid rgba(29,138,255,0.05);
}
.trace-event:last-child { border-bottom: none; }
.trace-event-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  margin-top: 3px;
  flex-shrink: 0;
}
.trace-event-dot.allow { background: var(--green); }
.trace-event-dot.deny  { background: var(--red); }
.trace-event-dot.info  { background: var(--blue); }
.trace-event-dot.policy { background: var(--amber); }
.trace-event-text { flex: 1; line-height: 1.4; color: var(--text); }
.trace-latency { font-size: 11px; color: var(--amber); margin-left: auto; }

/* ── Reduced motion ── */
@media (prefers-reduced-motion: reduce) {
  .content, .drawer, .drawer .toggle-track, .drawer .toggle-knob,
  .trace-panel, .trace-chevron, .btn-send, .btn-confirm, .btn-confirm {
    transition: none;
  }
  .nav-status-dot { animation: none; }
}
```

- [ ] **Step 10: Verify Next.js starts**

```bash
cd ui && npm run dev
```

Expected: server at `http://localhost:3000` (no page yet, but no startup errors).

- [ ] **Step 11: Commit**

```bash
git add ui/
git commit -m "feat(ui): scaffold Next.js app with design tokens"
```

---

### Task 8: Shared types + API client

**Files:**
- Create: `ui/src/lib/types.ts`
- Create: `ui/src/lib/api.ts`

- [ ] **Step 1: Create `ui/src/lib/types.ts`**

```typescript
export interface TickerData {
  ticker: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number;
}

export interface Holding {
  ticker: string;
  name: string;
  shares: number;
  cost_basis: number;
  current_price: number;
  market_value: number;
  pnl_pct: number;
}

export interface PortfolioData {
  holdings: Holding[];
  total_value: number;
}

export interface PolicyState {
  rbac: boolean;
  elicitation: boolean;
  rate_limit: boolean;
  guardrails: boolean;
}

export type PolicyKey = keyof PolicyState;

export interface PolicyEvent {
  type: string;
  policy: string;
  verdict: "allow" | "deny";
  message: string;
}

export interface TraceData {
  intent: "briefing" | "trade" | "unknown";
  agents: string[];
  latency_ms: number;
  status_code: number;
  policy_events: PolicyEvent[];
}

export interface ElicitationData {
  required: true;
  prompt: string;
  trade_details: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent_tag?: "BRIEFING" | "TRADE" | "ELICITATION";
  agent_name?: string;
  latency_ms?: number;
  policy_events?: PolicyEvent[];
  blocked?: boolean;
  elicitation?: ElicitationData;
}

export interface ChatRequest {
  message: string;
  session_id: string;
  confirmed?: boolean;
}

export interface ChatApiResponse {
  message: string;
  trace: TraceData;
  elicitation?: ElicitationData;
}
```

- [ ] **Step 2: Create `ui/src/lib/api.ts`**

```typescript
import type {
  TickerData,
  PortfolioData,
  PolicyState,
  PolicyKey,
  ChatRequest,
  ChatApiResponse,
} from "./types";

const BASE = "/api";

export async function fetchTickers(): Promise<TickerData[]> {
  const res = await fetch(`${BASE}/tickers`);
  if (!res.ok) throw new Error(`Tickers fetch failed: ${res.status}`);
  const data = await res.json();
  return data.tickers as TickerData[];
}

export async function fetchPortfolio(): Promise<PortfolioData> {
  const res = await fetch(`${BASE}/portfolio`);
  if (!res.ok) throw new Error(`Portfolio fetch failed: ${res.status}`);
  return res.json() as Promise<PortfolioData>;
}

export async function fetchPolicies(): Promise<PolicyState> {
  const res = await fetch(`${BASE}/policies`);
  if (!res.ok) throw new Error(`Policies fetch failed: ${res.status}`);
  return res.json() as Promise<PolicyState>;
}

export async function togglePolicy(
  key: PolicyKey,
  value: boolean
): Promise<PolicyState> {
  const res = await fetch(`${BASE}/policies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ [key]: value }),
  });
  if (!res.ok) throw new Error(`Policy update failed: ${res.status}`);
  return res.json() as Promise<PolicyState>;
}

export async function sendChat(req: ChatRequest): Promise<ChatApiResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Chat request failed: ${res.status}`);
  return res.json() as Promise<ChatApiResponse>;
}
```

- [ ] **Step 3: Commit**

```bash
git add ui/src/lib/
git commit -m "feat(ui): add shared types and API client"
```

---

### Task 9: NavBar component

**Files:**
- Create: `ui/src/components/NavBar.tsx`
- Create: `ui/src/__tests__/NavBar.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// ui/src/__tests__/NavBar.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import NavBar from "@/components/NavBar";

describe("NavBar", () => {
  it("renders FINFLOW wordmark", () => {
    render(<NavBar onPoliciesClick={() => {}} />);
    expect(screen.getByText("FINFLOW")).toBeInTheDocument();
  });

  it("renders agentgateway status label", () => {
    render(<NavBar onPoliciesClick={() => {}} />);
    expect(screen.getByText("agentgateway")).toBeInTheDocument();
  });

  it("calls onPoliciesClick when Policies button pressed", () => {
    const handler = jest.fn();
    render(<NavBar onPoliciesClick={handler} />);
    fireEvent.click(screen.getByRole("button", { name: /policies/i }));
    expect(handler).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd ui && npm test -- NavBar
```

Expected: `Cannot find module '@/components/NavBar'`

- [ ] **Step 3: Create `ui/src/components/NavBar.tsx`**

```tsx
interface NavBarProps {
  onPoliciesClick: () => void;
}

export default function NavBar({ onPoliciesClick }: NavBarProps) {
  return (
    <nav className="nav">
      <div className="nav-left">
        <button className="nav-policies-btn" onClick={onPoliciesClick}>
          Policies
        </button>
        <span className="nav-wordmark">FINFLOW</span>
      </div>
      <div className="nav-right">
        <span className="nav-status-dot" aria-label="agentgateway connected" />
        <span className="nav-status-label">agentgateway</span>
      </div>
    </nav>
  );
}
```

- [ ] **Step 4: Run test — verify it passes**

```bash
cd ui && npm test -- NavBar
```

Expected: all 3 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add ui/src/components/NavBar.tsx ui/src/__tests__/NavBar.test.tsx
git commit -m "feat(ui): add NavBar component"
```

---

### Task 10: TickerCard + useTickers hook

**Files:**
- Create: `ui/src/components/TickerCard.tsx`
- Create: `ui/src/hooks/useTickers.ts`
- Create: `ui/src/__tests__/TickerCard.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// ui/src/__tests__/TickerCard.test.tsx
import { render, screen } from "@testing-library/react";
import TickerCard from "@/components/TickerCard";

const nvda = { ticker: "NVDA", name: "NVIDIA Corp", price: 134.87, change_pct: 2.41, volume: 48203100 };
const aapl = { ticker: "AAPL", name: "Apple Inc", price: 211.50, change_pct: -0.83, volume: 52108400 };

describe("TickerCard", () => {
  it("renders ticker symbol", () => {
    render(<TickerCard ticker={nvda} />);
    expect(screen.getByText("NVDA")).toBeInTheDocument();
  });

  it("renders positive change in green class", () => {
    render(<TickerCard ticker={nvda} />);
    const change = screen.getByText(/\+2\.41%/);
    expect(change).toHaveClass("pos");
  });

  it("renders negative change in red class", () => {
    render(<TickerCard ticker={aapl} />);
    const change = screen.getByText(/−0\.83%/);
    expect(change).toHaveClass("neg");
  });
});
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd ui && npm test -- TickerCard
```

Expected: `Cannot find module '@/components/TickerCard'`

- [ ] **Step 3: Create `ui/src/components/TickerCard.tsx`**

```tsx
import type { TickerData } from "@/lib/types";

interface Props {
  ticker: TickerData;
}

export default function TickerCard({ ticker }: Props) {
  const isPos = ticker.change_pct >= 0;
  const sign = isPos ? "+" : "−";
  const abs = Math.abs(ticker.change_pct).toFixed(2);

  return (
    <div className="ticker-card">
      <div className="ticker-symbol">{ticker.ticker}</div>
      <div className="ticker-price">{ticker.price.toFixed(2)}</div>
      <div className={`ticker-change ${isPos ? "pos" : "neg"}`}>
        {sign}{abs}%
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create `ui/src/hooks/useTickers.ts`**

```typescript
"use client";
import { useState, useEffect } from "react";
import type { TickerData } from "@/lib/types";
import { fetchTickers } from "@/lib/api";

export function useTickers(refreshMs = 10_000) {
  const [tickers, setTickers] = useState<TickerData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        const data = await fetchTickers();
        if (alive) setTickers(data);
      } catch (e) {
        if (alive) setError(String(e));
      }
    }

    load();
    const id = setInterval(load, refreshMs);
    return () => { alive = false; clearInterval(id); };
  }, [refreshMs]);

  return { tickers, error };
}
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd ui && npm test -- TickerCard
```

Expected: all 3 tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add ui/src/components/TickerCard.tsx ui/src/hooks/useTickers.ts ui/src/__tests__/TickerCard.test.tsx
git commit -m "feat(ui): add TickerCard and useTickers hook"
```

---

### Task 11: PortfolioCard + usePortfolio + DataPanel

**Files:**
- Create: `ui/src/components/PortfolioCard.tsx`
- Create: `ui/src/hooks/usePortfolio.ts`
- Create: `ui/src/components/DataPanel.tsx`

- [ ] **Step 1: Create `ui/src/components/PortfolioCard.tsx`**

```tsx
import type { PortfolioData } from "@/lib/types";

interface Props {
  portfolio: PortfolioData;
}

export default function PortfolioCard({ portfolio }: Props) {
  return (
    <div className="portfolio-card">
      <div className="section-label">Portfolio</div>
      <div className="portfolio-value">
        ${portfolio.total_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
      {portfolio.holdings.map((h) => (
        <div key={h.ticker} className="portfolio-row">
          <div>
            <span className="portfolio-ticker">{h.ticker}</span>
            <span className="portfolio-shares"> · {h.shares} sh</span>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="portfolio-value-cell">
              ${h.market_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className={`portfolio-pnl ${h.pnl_pct >= 0 ? "pos" : "neg"}`}>
              {h.pnl_pct >= 0 ? "+" : ""}{h.pnl_pct.toFixed(2)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create `ui/src/hooks/usePortfolio.ts`**

```typescript
"use client";
import { useState, useEffect } from "react";
import type { PortfolioData } from "@/lib/types";
import { fetchPortfolio } from "@/lib/api";

export function usePortfolio(refreshMs = 30_000) {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        const data = await fetchPortfolio();
        if (alive) setPortfolio(data);
      } catch (e) {
        if (alive) setError(String(e));
      }
    }

    load();
    const id = setInterval(load, refreshMs);
    return () => { alive = false; clearInterval(id); };
  }, [refreshMs]);

  return { portfolio, error };
}
```

- [ ] **Step 3: Create `ui/src/components/DataPanel.tsx`**

```tsx
"use client";
import TickerCard from "./TickerCard";
import PortfolioCard from "./PortfolioCard";
import { useTickers } from "@/hooks/useTickers";
import { usePortfolio } from "@/hooks/usePortfolio";

export default function DataPanel() {
  const { tickers } = useTickers();
  const { portfolio } = usePortfolio();

  return (
    <div className="data-panel">
      <div>
        <div className="section-label">Market</div>
        <div className="ticker-grid">
          {tickers.map((t) => (
            <TickerCard key={t.ticker} ticker={t} />
          ))}
        </div>
      </div>
      {portfolio && <PortfolioCard portfolio={portfolio} />}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add ui/src/components/PortfolioCard.tsx ui/src/hooks/usePortfolio.ts ui/src/components/DataPanel.tsx
git commit -m "feat(ui): add PortfolioCard, usePortfolio, DataPanel"
```

---

### Task 12: ChatBubble + ChatInput + useChat

**Files:**
- Create: `ui/src/components/ChatBubble.tsx`
- Create: `ui/src/components/ChatInput.tsx`
- Create: `ui/src/hooks/useChat.ts`
- Create: `ui/src/__tests__/ChatBubble.test.tsx`
- Create: `ui/src/__tests__/ChatInput.test.tsx`
- Create: `ui/src/__tests__/useChat.test.ts`

- [ ] **Step 1: Write failing tests**

```tsx
// ui/src/__tests__/ChatBubble.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import ChatBubble from "@/components/ChatBubble";
import type { ChatMessage } from "@/lib/types";

const userMsg: ChatMessage = {
  id: "1", role: "user", content: "Show my portfolio",
};
const aiMsg: ChatMessage = {
  id: "2", role: "assistant", content: "Portfolio up 2.3%",
  agent_tag: "BRIEFING", agent_name: "portfolio-agent", latency_ms: 340,
};
const blockedMsg: ChatMessage = {
  id: "3", role: "assistant", content: "Request denied.",
  agent_tag: "TRADE", blocked: true,
};

describe("ChatBubble", () => {
  it("renders user bubble with bubble-user class", () => {
    const { container } = render(<ChatBubble message={userMsg} onConfirm={() => {}} />);
    expect(container.querySelector(".bubble-user")).toBeInTheDocument();
    expect(screen.getByText("Show my portfolio")).toBeInTheDocument();
  });

  it("renders AI bubble with agent tag and latency", () => {
    render(<ChatBubble message={aiMsg} onConfirm={() => {}} />);
    expect(screen.getByText("BRIEFING")).toBeInTheDocument();
    expect(screen.getByText("portfolio-agent")).toBeInTheDocument();
    expect(screen.getByText("340ms")).toBeInTheDocument();
  });

  it("renders blocked bubble with blocked class", () => {
    const { container } = render(<ChatBubble message={blockedMsg} onConfirm={() => {}} />);
    expect(container.querySelector(".bubble-blocked")).toBeInTheDocument();
  });
});
```

```tsx
// ui/src/__tests__/ChatInput.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatInput from "@/components/ChatInput";

describe("ChatInput", () => {
  it("calls onSend with typed message on Enter", async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);
    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "hello");
    await user.keyboard("{Enter}");
    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("does not send on Shift+Enter (newline)", async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);
    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "line1");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables send button when disabled=true", () => {
    render(<ChatInput onSend={() => {}} disabled={true} />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
```

```typescript
// ui/src/__tests__/useChat.test.ts
import { renderHook, act } from "@testing-library/react";
import { useChat } from "@/hooks/useChat";

global.fetch = jest.fn();

afterEach(() => jest.clearAllMocks());

describe("useChat", () => {
  it("adds user message immediately on send", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: "Portfolio up 2.3%",
        trace: { intent: "briefing", agents: ["portfolio-agent"], latency_ms: 340, status_code: 200, policy_events: [] },
        elicitation: null,
      }),
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.send("show portfolio");
    });

    const msgs = result.current.messages;
    expect(msgs[0].role).toBe("user");
    expect(msgs[0].content).toBe("show portfolio");
    expect(msgs[1].role).toBe("assistant");
    expect(msgs[1].content).toBe("Portfolio up 2.3%");
  });

  it("sets elicitation state when returned", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: "Confirmation required.",
        trace: { intent: "trade", agents: [], latency_ms: 20, status_code: 200, policy_events: [{ type: "elicitation_required", policy: "Elicitation", verdict: "allow", message: "..." }] },
        elicitation: { required: true, prompt: "Confirm trade", trade_details: "BUY 10 NVDA" },
      }),
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.send("buy 10 NVDA");
    });

    const lastMsg = result.current.messages[result.current.messages.length - 1];
    expect(lastMsg.elicitation).toBeDefined();
    expect(lastMsg.elicitation?.trade_details).toBe("BUY 10 NVDA");
  });
});
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd ui && npm test -- ChatBubble ChatInput useChat
```

Expected: `Cannot find module` errors

- [ ] **Step 3: Create `ui/src/components/ChatBubble.tsx`**

```tsx
import type { ChatMessage } from "@/lib/types";

interface Props {
  message: ChatMessage;
  onConfirm: (id: string) => void;
}

function tagClass(tag?: string, blocked?: boolean): string {
  if (blocked) return "agent-tag agent-tag-blocked";
  if (tag === "ELICITATION") return "agent-tag agent-tag-policy";
  return "agent-tag";
}

export default function ChatBubble({ message, onConfirm }: Props) {
  if (message.role === "user") {
    return (
      <div className="bubble bubble-user">
        {message.content}
      </div>
    );
  }

  return (
    <div className={`bubble bubble-ai${message.blocked ? " bubble-blocked" : ""}`}>
      {message.agent_tag && (
        <div className="bubble-meta">
          <span className={tagClass(message.agent_tag, message.blocked)}>
            {message.agent_tag}
          </span>
          {message.agent_name && (
            <span className="bubble-agent">{message.agent_name}</span>
          )}
          {message.latency_ms !== undefined && (
            <span className="bubble-latency">{message.latency_ms}ms</span>
          )}
        </div>
      )}
      <div>
        {message.blocked
          ? <><span className="bubble-denied">Request denied.</span> <span className="bubble-muted">{message.content.replace("Request denied.", "").trim()}</span></>
          : message.content
        }
      </div>
      {message.elicitation && (
        <>
          <div style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
            {message.elicitation.trade_details}
          </div>
          <button className="btn-confirm" onClick={() => onConfirm(message.id)}>
            Confirm
          </button>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Create `ui/src/components/ChatInput.tsx`**

```tsx
import { useRef, KeyboardEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const text = ref.current?.value.trim();
    if (!text || disabled) return;
    onSend(text);
    if (ref.current) ref.current.value = "";
  }

  return (
    <>
      <textarea
        ref={ref}
        className="chat-input"
        placeholder="Ask about your portfolio, request a trade…"
        rows={1}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-label="Chat input"
      />
      <button
        className="btn-send"
        onClick={submit}
        disabled={disabled}
        aria-label="Send"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M2 8h12M10 4l4 4-4 4"
            stroke="#fff"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </>
  );
}
```

- [ ] **Step 5: Create `ui/src/hooks/useChat.ts`**

```typescript
"use client";
import { useState, useCallback, useRef } from "react";
import type { ChatMessage, ChatApiResponse } from "@/lib/types";
import { sendChat } from "@/lib/api";

function uid() {
  return Math.random().toString(36).slice(2);
}

function agentTag(intent: string, blocked: boolean): ChatMessage["agent_tag"] {
  if (blocked) return "TRADE";
  if (intent === "briefing") return "BRIEFING";
  if (intent === "trade") return "TRADE";
  return undefined;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastTrace, setLastTrace] = useState<ChatApiResponse["trace"] | null>(null);
  const sessionId = useRef(uid());

  const appendMsg = (msg: ChatMessage) =>
    setMessages((prev) => [...prev, msg]);

  const send = useCallback(async (text: string, confirmed = false) => {
    appendMsg({ id: uid(), role: "user", content: text });
    setLoading(true);

    try {
      const resp = await sendChat({
        message: text,
        session_id: sessionId.current,
        confirmed,
      });

      setLastTrace(resp.trace);
      const blocked = resp.trace.status_code === 403 || resp.trace.status_code === 400;
      const intent = resp.trace.intent;

      appendMsg({
        id: uid(),
        role: "assistant",
        content: resp.message,
        agent_tag: resp.elicitation ? "ELICITATION" : agentTag(intent, blocked),
        agent_name: resp.elicitation ? undefined : (resp.trace.agents[0] ?? undefined),
        latency_ms: resp.trace.latency_ms,
        policy_events: resp.trace.policy_events,
        blocked,
        elicitation: resp.elicitation,
      });
    } catch {
      appendMsg({
        id: uid(),
        role: "assistant",
        content: "Error: could not reach BFF. Is it running on port 8001?",
        blocked: true,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const confirm = useCallback(async (msgId: string) => {
    const msg = messages.find((m) => m.id === msgId);
    if (!msg?.elicitation) return;
    // Remove elicitation from the confirmed message
    setMessages((prev) =>
      prev.map((m) => m.id === msgId ? { ...m, elicitation: undefined } : m)
    );
    // Find the original user message (one before this assistant message)
    const idx = messages.findIndex((m) => m.id === msgId);
    const userMsg = idx > 0 ? messages[idx - 1] : null;
    if (userMsg?.role === "user") {
      await send(userMsg.content, true);
    }
  }, [messages, send]);

  return { messages, loading, lastTrace, send, confirm };
}
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
cd ui && npm test -- ChatBubble ChatInput useChat
```

Expected: all tests `PASSED`

- [ ] **Step 7: Commit**

```bash
git add ui/src/components/ChatBubble.tsx ui/src/components/ChatInput.tsx ui/src/hooks/useChat.ts ui/src/__tests__/ChatBubble.test.tsx ui/src/__tests__/ChatInput.test.tsx ui/src/__tests__/useChat.test.ts
git commit -m "feat(ui): add ChatBubble, ChatInput, useChat hook"
```

---

### Task 13: ChatPanel

**Files:**
- Create: `ui/src/components/ChatPanel.tsx`

- [ ] **Step 1: Create `ui/src/components/ChatPanel.tsx`**

```tsx
"use client";
import { useEffect, useRef } from "react";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import type { ChatMessage, TraceData } from "@/lib/types";

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
  onConfirm: (id: string) => void;
}

export default function ChatPanel({ messages, loading, onSend, onConfirm }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div style={{ color: "var(--muted)", fontSize: 12, textAlign: "center", marginTop: 40 }}>
            Ask about your portfolio or request a trade.
          </div>
        )}
        {messages.map((m) => (
          <ChatBubble key={m.id} message={m} onConfirm={onConfirm} />
        ))}
        {loading && (
          <div className="bubble bubble-ai" style={{ opacity: 0.5 }}>
            <div className="bubble-meta">
              <span className="agent-tag">···</span>
            </div>
            Thinking…
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="chat-footer">
        <ChatInput onSend={onSend} disabled={loading} />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add ui/src/components/ChatPanel.tsx
git commit -m "feat(ui): add ChatPanel"
```

---

### Task 14: PolicyDrawer + usePolicies

**Files:**
- Create: `ui/src/components/PolicyRow.tsx`
- Create: `ui/src/components/PolicyDrawer.tsx`
- Create: `ui/src/hooks/usePolicies.ts`
- Create: `ui/src/__tests__/PolicyDrawer.test.tsx`
- Create: `ui/src/__tests__/usePolicies.test.ts`

- [ ] **Step 1: Write failing tests**

```tsx
// ui/src/__tests__/PolicyDrawer.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import PolicyDrawer from "@/components/PolicyDrawer";
import type { PolicyState } from "@/lib/types";

const policies: PolicyState = { rbac: false, elicitation: true, rate_limit: false, guardrails: false };

describe("PolicyDrawer", () => {
  it("renders all four policy names", () => {
    render(
      <PolicyDrawer open={true} policies={policies} onClose={() => {}} onToggle={() => {}} />
    );
    expect(screen.getByText("MCP RBAC")).toBeInTheDocument();
    expect(screen.getByText("Elicitation")).toBeInTheDocument();
    expect(screen.getByText("Rate Limits")).toBeInTheDocument();
    expect(screen.getByText("Guardrails")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", () => {
    const onClose = jest.fn();
    render(
      <PolicyDrawer open={true} policies={policies} onClose={onClose} onToggle={() => {}} />
    );
    fireEvent.click(screen.getByLabelText(/close policies/i));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onToggle with key and new value when toggle clicked", () => {
    const onToggle = jest.fn();
    render(
      <PolicyDrawer open={true} policies={policies} onClose={() => {}} onToggle={onToggle} />
    );
    // RBAC is off (false) — click its toggle → expect (rbac, true)
    const toggles = screen.getAllByRole("checkbox");
    fireEvent.click(toggles[0]); // first is RBAC
    expect(onToggle).toHaveBeenCalledWith("rbac", true);
  });
});
```

```typescript
// ui/src/__tests__/usePolicies.test.ts
import { renderHook, act } from "@testing-library/react";
import { usePolicies } from "@/hooks/usePolicies";

global.fetch = jest.fn();
afterEach(() => jest.clearAllMocks());

describe("usePolicies", () => {
  it("fetches policies on mount", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ rbac: false, elicitation: false, rate_limit: false, guardrails: false }),
    });
    const { result } = renderHook(() => usePolicies());
    await act(async () => {});
    expect(result.current.policies).toEqual({ rbac: false, elicitation: false, rate_limit: false, guardrails: false });
  });

  it("toggle calls POST and updates state", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ rbac: false, elicitation: false, rate_limit: false, guardrails: false }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ rbac: true, elicitation: false, rate_limit: false, guardrails: false }) });

    const { result } = renderHook(() => usePolicies());
    await act(async () => {});
    await act(async () => { await result.current.toggle("rbac", true); });
    expect(result.current.policies?.rbac).toBe(true);
  });
});
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd ui && npm test -- PolicyDrawer usePolicies
```

Expected: `Cannot find module` errors

- [ ] **Step 3: Create `ui/src/components/PolicyRow.tsx`**

```tsx
import type { PolicyKey } from "@/lib/types";

interface Props {
  label: string;
  description: string;
  policyKey: PolicyKey;
  checked: boolean;
  onToggle: (key: PolicyKey, value: boolean) => void;
}

export default function PolicyRow({ label, description, policyKey, checked, onToggle }: Props) {
  return (
    <div className="policy-row">
      <div className="policy-info">
        <div className="policy-name">{label}</div>
        <div className="policy-desc">{description}</div>
      </div>
      <label className="toggle" aria-label={`Toggle ${label}`}>
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onToggle(policyKey, e.target.checked)}
        />
        <span className="toggle-track">
          <span className="toggle-knob" />
        </span>
      </label>
    </div>
  );
}
```

- [ ] **Step 4: Create `ui/src/components/PolicyDrawer.tsx`**

```tsx
import PolicyRow from "./PolicyRow";
import type { PolicyState, PolicyKey } from "@/lib/types";

interface Props {
  open: boolean;
  policies: PolicyState;
  onClose: () => void;
  onToggle: (key: PolicyKey, value: boolean) => void;
}

const POLICY_DEFS: { key: PolicyKey; label: string; desc: string }[] = [
  { key: "rbac", label: "MCP RBAC", desc: "Restrict TRADE agent to authorized roles" },
  { key: "elicitation", label: "Elicitation", desc: "Require confirmation before executing trades" },
  { key: "rate_limit", label: "Rate Limits", desc: "10 req/min per virtual key" },
  { key: "guardrails", label: "Guardrails", desc: "Block financial advice language" },
];

export default function PolicyDrawer({ open, policies, onClose, onToggle }: Props) {
  return (
    <aside className={`drawer${open ? " open" : ""}`} aria-hidden={!open}>
      <div className="drawer-header">
        <span className="drawer-title">Policies</span>
        <button className="drawer-close" onClick={onClose} aria-label="Close policies">
          ×
        </button>
      </div>
      <div className="drawer-body">
        {POLICY_DEFS.map((p) => (
          <PolicyRow
            key={p.key}
            label={p.label}
            description={p.desc}
            policyKey={p.key}
            checked={policies[p.key]}
            onToggle={onToggle}
          />
        ))}
      </div>
    </aside>
  );
}
```

- [ ] **Step 5: Create `ui/src/hooks/usePolicies.ts`**

```typescript
"use client";
import { useState, useEffect, useCallback } from "react";
import type { PolicyState, PolicyKey } from "@/lib/types";
import { fetchPolicies, togglePolicy } from "@/lib/api";

export function usePolicies() {
  const [policies, setPolicies] = useState<PolicyState | null>(null);

  useEffect(() => {
    fetchPolicies().then(setPolicies).catch(console.error);
  }, []);

  const toggle = useCallback(async (key: PolicyKey, value: boolean) => {
    const updated = await togglePolicy(key, value);
    setPolicies(updated);
  }, []);

  return { policies, toggle };
}
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
cd ui && npm test -- PolicyDrawer usePolicies
```

Expected: all tests `PASSED`

- [ ] **Step 7: Commit**

```bash
git add ui/src/components/PolicyRow.tsx ui/src/components/PolicyDrawer.tsx ui/src/hooks/usePolicies.ts ui/src/__tests__/PolicyDrawer.test.tsx ui/src/__tests__/usePolicies.test.ts
git commit -m "feat(ui): add PolicyDrawer, PolicyRow, usePolicies hook"
```

---

### Task 15: TracePanel

**Files:**
- Create: `ui/src/components/TracePanel.tsx`
- Create: `ui/src/__tests__/TracePanel.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// ui/src/__tests__/TracePanel.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import TracePanel from "@/components/TracePanel";
import type { TraceData } from "@/lib/types";

const trace: TraceData = {
  intent: "briefing",
  agents: ["portfolio-agent", "market-data-agent"],
  latency_ms: 480,
  status_code: 200,
  policy_events: [],
};

const blockedTrace: TraceData = {
  intent: "trade",
  agents: [],
  latency_ms: 12,
  status_code: 403,
  policy_events: [{ type: "rbac_block", policy: "MCP RBAC", verdict: "deny", message: "Requires trade role" }],
};

describe("TracePanel", () => {
  it("renders collapsed summary with intent and latency", () => {
    render(<TracePanel trace={trace} />);
    expect(screen.getByText(/briefing/i)).toBeInTheDocument();
    expect(screen.getByText(/480ms/)).toBeInTheDocument();
  });

  it("expands when bar is clicked", () => {
    const { container } = render(<TracePanel trace={trace} />);
    const panel = container.querySelector(".trace-panel");
    expect(panel).not.toHaveClass("open");
    fireEvent.click(container.querySelector(".trace-bar")!);
    expect(panel).toHaveClass("open");
  });

  it("shows policy events in expanded view", () => {
    const { container } = render(<TracePanel trace={blockedTrace} />);
    fireEvent.click(container.querySelector(".trace-bar")!);
    expect(screen.getByText(/MCP RBAC/i)).toBeInTheDocument();
    expect(screen.getByText(/Requires trade role/i)).toBeInTheDocument();
  });

  it("shows agents in request flow column", () => {
    const { container } = render(<TracePanel trace={trace} />);
    fireEvent.click(container.querySelector(".trace-bar")!);
    expect(screen.getByText("portfolio-agent")).toBeInTheDocument();
    expect(screen.getByText("market-data-agent")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd ui && npm test -- TracePanel
```

Expected: `Cannot find module '@/components/TracePanel'`

- [ ] **Step 3: Create `ui/src/components/TracePanel.tsx`**

```tsx
"use client";
import { useState } from "react";
import type { TraceData } from "@/lib/types";

interface Props {
  trace: TraceData | null;
}

function dotClass(verdict: string): string {
  if (verdict === "deny") return "trace-event-dot deny";
  if (verdict === "allow") return "trace-event-dot allow";
  return "trace-event-dot info";
}

export default function TracePanel({ trace }: Props) {
  const [open, setOpen] = useState(false);

  const summary = trace
    ? `${trace.intent} · ${trace.agents.length} agent${trace.agents.length !== 1 ? "s" : ""} · ${trace.latency_ms}ms`
    : "No trace yet";

  return (
    <div className={`trace-panel${open ? " open" : ""}`}>
      <div
        className="trace-bar"
        role="button"
        tabIndex={0}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => e.key === "Enter" && setOpen((v) => !v)}
      >
        <span className="trace-summary">{summary}</span>
        <span className="trace-chevron">▲</span>
      </div>

      {open && trace && (
        <div className="trace-body">
          <div>
            <div className="trace-col-label">Request Flow</div>
            {trace.agents.length === 0 && (
              <div className="trace-event">
                <span className="trace-event-dot deny" />
                <span className="trace-event-text">No agents called</span>
              </div>
            )}
            {trace.agents.map((a, i) => (
              <div key={i} className="trace-event">
                <span className="trace-event-dot allow" />
                <span className="trace-event-text">{a}</span>
              </div>
            ))}
            <div className="trace-event" style={{ marginTop: 4 }}>
              <span className="trace-event-dot info" />
              <span className="trace-event-text">
                HTTP {trace.status_code} · {trace.latency_ms}ms
              </span>
            </div>
          </div>

          <div>
            <div className="trace-col-label">Auth &amp; Routing</div>
            {trace.policy_events.length === 0 ? (
              <div className="trace-event">
                <span className="trace-event-dot allow" />
                <span className="trace-event-text">No policy events</span>
              </div>
            ) : (
              trace.policy_events.map((ev, i) => (
                <div key={i} className="trace-event">
                  <span className={dotClass(ev.verdict)} />
                  <div className="trace-event-text">
                    <div style={{ fontWeight: 600 }}>{ev.policy}</div>
                    <div style={{ color: "var(--muted)" }}>{ev.message}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run test — verify it passes**

```bash
cd ui && npm test -- TracePanel
```

Expected: all 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add ui/src/components/TracePanel.tsx ui/src/__tests__/TracePanel.test.tsx
git commit -m "feat(ui): add TracePanel with expand/collapse"
```

---

### Task 16: page.tsx — wire all panels

**Files:**
- Create: `ui/src/app/page.tsx`

- [ ] **Step 1: Create `ui/src/app/page.tsx`**

```tsx
"use client";
import { useState } from "react";
import NavBar from "@/components/NavBar";
import ChatPanel from "@/components/ChatPanel";
import DataPanel from "@/components/DataPanel";
import PolicyDrawer from "@/components/PolicyDrawer";
import TracePanel from "@/components/TracePanel";
import { useChat } from "@/hooks/useChat";
import { usePolicies } from "@/hooks/usePolicies";

export default function Page() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { messages, loading, lastTrace, send, confirm } = useChat();
  const { policies, toggle } = usePolicies();

  return (
    <div className="app-shell">
      <NavBar onPoliciesClick={() => setDrawerOpen((v) => !v)} />

      <div className="layout">
        <PolicyDrawer
          open={drawerOpen}
          policies={policies ?? { rbac: false, elicitation: false, rate_limit: false, guardrails: false }}
          onClose={() => setDrawerOpen(false)}
          onToggle={toggle}
        />

        <div className={`content${drawerOpen ? " pushed" : ""}`}>
          <ChatPanel
            messages={messages}
            loading={loading}
            onSend={send}
            onConfirm={confirm}
          />
          <DataPanel />
        </div>

        <TracePanel trace={lastTrace} />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify dev server renders without errors**

```bash
cd ui && npm run dev
```

Open `http://localhost:3000` — expect: Signal Room layout visible, nav with FINFLOW wordmark + Policies button, split chat/data panels, trace bar at bottom.

- [ ] **Step 3: Run full test suite**

```bash
cd ui && npm test
```

Expected: all tests `PASSED`

- [ ] **Step 4: Commit**

```bash
git add ui/src/app/page.tsx
git commit -m "feat(ui): wire all panels in page.tsx"
```

---

### Task 17: Docker + k8s manifests

**Files:**
- Create: `ui/Dockerfile`
- Create: `infra/k8s/base/bff.yaml`
- Create: `infra/k8s/base/ui.yaml`
- Modify: `infra/k8s/base/kustomization.yaml`

- [ ] **Step 1: Create `ui/Dockerfile`**

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

- [ ] **Step 2: Add `output: "standalone"` to `ui/next.config.ts`**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const bffUrl = process.env.BFF_URL ?? "http://localhost:8001";
    return [
      { source: "/api/:path*", destination: `${bffUrl}/api/:path*` },
    ];
  },
};

export default nextConfig;
```

- [ ] **Step 3: Create `infra/k8s/base/bff.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finflow-bff
  namespace: finflow
  labels:
    app: finflow-bff
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: finflow-bff
  template:
    metadata:
      labels:
        app: finflow-bff
    spec:
      containers:
        - name: bff
          image: finflow/bff:latest
          ports:
            - containerPort: 8001
          env:
            - name: ORCHESTRATOR_URL
              value: "http://finflow-orchestrator:8000"
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /api/health
              port: 8001
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: finflow-bff
  namespace: finflow
  labels:
    app: finflow-bff
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: finflow-bff
  ports:
    - port: 8001
      targetPort: 8001
  type: ClusterIP
```

- [ ] **Step 4: Create `infra/k8s/base/ui.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finflow-ui
  namespace: finflow
  labels:
    app: finflow-ui
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: finflow-ui
  template:
    metadata:
      labels:
        app: finflow-ui
    spec:
      containers:
        - name: ui
          image: finflow/ui:latest
          ports:
            - containerPort: 3000
          env:
            - name: BFF_URL
              value: "http://finflow-bff:8001"
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: finflow-ui
  namespace: finflow
  labels:
    app: finflow-ui
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: finflow-ui
  ports:
    - port: 3000
      targetPort: 3000
  type: ClusterIP
```

- [ ] **Step 5: Verify Makefile additions compile**

```bash
make test-bff
```

Expected: BFF tests pass.

- [ ] **Step 6: Final commit**

```bash
git add ui/Dockerfile ui/next.config.ts infra/k8s/base/bff.yaml infra/k8s/base/ui.yaml
git commit -m "feat: add Docker and k8s manifests for BFF and UI"
```

---

## Self-Review

### Spec coverage

| Requirement | Task |
|---|---|
| Single-page layout: Chat (left) + Data (right) | Task 16 page.tsx |
| Policies left sliding drawer | Task 14 PolicyDrawer |
| Trace bottom overlay (absolute, not push) | Task 15 TracePanel (position:absolute in CSS) |
| Nav: Policies button + FINFLOW wordmark + agentgateway dot | Task 9 NavBar |
| Ticker cards with market data | Task 10 TickerCard |
| Portfolio value + holdings list | Task 11 PortfolioCard |
| Chat bubbles: user/AI/RBAC-blocked/elicitation | Task 12 ChatBubble |
| RBAC policy enforcement | Task 5 /api/chat |
| Elicitation confirmation flow | Tasks 5 + 12 + 14 |
| Guardrails keyword block | Task 5 /api/chat |
| Rate limit demo event | Task 5 /api/chat |
| BFF-side trace only | Task 5 TraceCapture |
| Policy state toggleable from UI | Tasks 4 + 14 |
| Proxy to existing orchestrator | Task 5 /api/chat |
| Mock data from infra/mock-data/ | Task 2 mock.py |
| Design tokens (Signal Room palette) | Task 7 globals.css |

### Placeholder check

None found — every step contains complete code or exact commands.

### Type consistency check

- `PolicyKey` used in `PolicyRow`, `PolicyDrawer`, `usePolicies`, `api.ts` — all use `keyof PolicyState` ✓
- `ChatMessage.agent_tag` type `"BRIEFING" | "TRADE" | "ELICITATION" | undefined` — used consistently in `ChatBubble` and `useChat` ✓
- `TraceData` shape defined once in `types.ts`, matched exactly by BFF `models.py` `TraceData` ✓
- `ElicitationData.required` is `true` (literal) in types.ts, `bool = True` in models.py ✓
- `useChat.confirm()` references `messages` from same hook state ✓

---

**Plan complete and saved to `docs/superpowers/plans/2026-06-07-finflow-ui.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
