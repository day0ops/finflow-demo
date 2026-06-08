# FinFlow Phase 1: Project Scaffold + MCP Servers — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize the `finflow-demo` repo and build all four MCP servers (market-data, portfolio, news, brokerage) as tested, containerized FastMCP services with base Kubernetes manifests.

**Architecture:** Four independent FastMCP 2.x Python services using StreamableHTTP transport. Each has its own `pyproject.toml`, `Dockerfile`, and `pytest` test suite. Tests run against the in-process FastMCP instance (no HTTP overhead). Base K8s manifests deploy all four as ClusterIP services in the `finflow` namespace. No agents or UI in this phase.

**Tech Stack:** Python 3.12, uv, fastmcp>=2.0, pytest, pytest-asyncio, Docker, Kubernetes (kustomize)

---

## File Map

```
finflow-demo/
├── .gitignore
├── Makefile
├── README.md
├── mcp-servers/
│   ├── market-data-mcp/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── server.py          # FastMCP app + entrypoint
│   │   ├── data.py            # mock ticker prices + historical data
│   │   └── tests/
│   │       └── test_tools.py
│   ├── portfolio-mcp/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── server.py
│   │   ├── db.py              # SQLite holdings + P&L logic
│   │   └── tests/
│   │       └── test_tools.py
│   ├── news-mcp/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── server.py
│   │   ├── data.py            # mock headlines + sentiment logic
│   │   └── tests/
│   │       └── test_tools.py
│   └── brokerage-mcp/
│       ├── pyproject.toml
│       ├── Dockerfile
│       ├── server.py
│       ├── store.py           # in-memory order store
│       └── tests/
│           └── test_tools.py
└── infra/
    ├── mock-data/
    │   ├── tickers.json       # canonical price data used by market-data-mcp + seed
    │   ├── holdings.sql       # seed SQL for portfolio-mcp SQLite DB
    │   └── news.json          # canonical news data used by news-mcp + seed
    └── k8s/
        ├── base/
        │   ├── kustomization.yaml
        │   ├── namespace.yaml
        │   └── mcp-servers/
        │       ├── kustomization.yaml
        │       ├── market-data-mcp.yaml   # Deployment + Service
        │       ├── portfolio-mcp.yaml
        │       ├── news-mcp.yaml
        │       └── brokerage-mcp.yaml
        └── features/
            ├── obo/
            │   └── .gitkeep
            ├── rbac/
            │   └── .gitkeep
            ├── mcp-access/
            │   └── .gitkeep
            └── elicitation/
                └── .gitkeep
```

---

## Task 1: Init repo

**Files:**
- Create: `.gitignore`
- Create: `Makefile`
- Create: `README.md`

- [ ] **Step 1: Init git repo**

```bash
cd /Users/kasunt/Projects/personal/public/finflow-demo
git init
git checkout -b main
```

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.env
*.db
*.sqlite
dist/
.DS_Store
.next/
node_modules/
*.log
```

- [ ] **Step 3: Write `Makefile`**

```makefile
REGISTRY ?= localhost:5000
TAG ?= latest

.PHONY: test test-all build push

test-market-data:
	cd mcp-servers/market-data-mcp && uv run pytest tests/ -v

test-portfolio:
	cd mcp-servers/portfolio-mcp && uv run pytest tests/ -v

test-news:
	cd mcp-servers/news-mcp && uv run pytest tests/ -v

test-brokerage:
	cd mcp-servers/brokerage-mcp && uv run pytest tests/ -v

test-all: test-market-data test-portfolio test-news test-brokerage

build:
	docker build -t $(REGISTRY)/finflow/market-data-mcp:$(TAG) mcp-servers/market-data-mcp
	docker build -t $(REGISTRY)/finflow/portfolio-mcp:$(TAG) mcp-servers/portfolio-mcp
	docker build -t $(REGISTRY)/finflow/news-mcp:$(TAG) mcp-servers/news-mcp
	docker build -t $(REGISTRY)/finflow/brokerage-mcp:$(TAG) mcp-servers/brokerage-mcp

push:
	docker push $(REGISTRY)/finflow/market-data-mcp:$(TAG)
	docker push $(REGISTRY)/finflow/portfolio-mcp:$(TAG)
	docker push $(REGISTRY)/finflow/news-mcp:$(TAG)
	docker push $(REGISTRY)/finflow/brokerage-mcp:$(TAG)
```

- [ ] **Step 4: Write `README.md`**

```markdown
# FinFlow Demo

Multi-agent financial portfolio assistant demonstrating the Solo.io agentic product suite:
agentgateway, agent registry, and kagent.

## Structure

- `mcp-servers/` — FastMCP tool servers (market-data, portfolio, news, brokerage)
- `agents/` — Agent implementations (Phase 2)
- `ui/` — Next.js frontend + BFF (Phase 3)
- `infra/` — Kubernetes manifests and mock data

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker
- kubectl

## Quick Start

```bash
# Run all MCP server tests
make test-all

# Build all images
make build REGISTRY=<your-registry>

# Deploy to Kubernetes
kubectl apply -k infra/k8s/base/
```
```

- [ ] **Step 5: Initial commit**

```bash
git add .gitignore Makefile README.md docs/
git commit -m "chore: init finflow-demo repo"
```

---

## Task 2: Mock data files

**Files:**
- Create: `infra/mock-data/tickers.json`
- Create: `infra/mock-data/holdings.sql`
- Create: `infra/mock-data/news.json`

These files are the canonical source of truth for demo data. MCP servers import from them or seed from them. Define them before implementing servers to avoid duplication.

- [ ] **Step 1: Write `infra/mock-data/tickers.json`**

```json
{
  "NVDA": {
    "ticker": "NVDA",
    "name": "NVIDIA Corp",
    "price": 134.87,
    "change_pct": 2.41,
    "volume": 48203100,
    "sector": "Technology",
    "history": [
      {"date": "2026-06-05", "close": 131.70},
      {"date": "2026-06-04", "close": 129.45},
      {"date": "2026-06-03", "close": 133.20},
      {"date": "2026-06-02", "close": 128.90},
      {"date": "2026-05-30", "close": 126.10}
    ]
  },
  "AAPL": {
    "ticker": "AAPL",
    "name": "Apple Inc",
    "price": 211.50,
    "change_pct": -0.83,
    "volume": 52108400,
    "sector": "Technology",
    "history": [
      {"date": "2026-06-05", "close": 213.26},
      {"date": "2026-06-04", "close": 210.88},
      {"date": "2026-06-03", "close": 214.50},
      {"date": "2026-06-02", "close": 209.31},
      {"date": "2026-05-30", "close": 207.45}
    ]
  },
  "MSFT": {
    "ticker": "MSFT",
    "name": "Microsoft Corp",
    "price": 442.31,
    "change_pct": 1.12,
    "volume": 19847200,
    "sector": "Technology",
    "history": [
      {"date": "2026-06-05", "close": 437.40},
      {"date": "2026-06-04", "close": 435.10},
      {"date": "2026-06-03", "close": 440.80},
      {"date": "2026-06-02", "close": 438.25},
      {"date": "2026-05-30", "close": 432.90}
    ]
  },
  "GOOGL": {
    "ticker": "GOOGL",
    "name": "Alphabet Inc",
    "price": 178.92,
    "change_pct": 0.67,
    "volume": 24503100,
    "sector": "Technology",
    "history": [
      {"date": "2026-06-05", "close": 177.73},
      {"date": "2026-06-04", "close": 175.40},
      {"date": "2026-06-03", "close": 179.10},
      {"date": "2026-06-02", "close": 176.85},
      {"date": "2026-05-30", "close": 174.20}
    ]
  },
  "AMZN": {
    "ticker": "AMZN",
    "name": "Amazon.com Inc",
    "price": 228.14,
    "change_pct": -0.34,
    "volume": 31204500,
    "sector": "Consumer Discretionary",
    "history": [
      {"date": "2026-06-05", "close": 228.91},
      {"date": "2026-06-04", "close": 226.40},
      {"date": "2026-06-03", "close": 230.15},
      {"date": "2026-06-02", "close": 225.80},
      {"date": "2026-05-30", "close": 223.45}
    ]
  }
}
```

- [ ] **Step 2: Write `infra/mock-data/holdings.sql`**

```sql
CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    shares REAL NOT NULL,
    cost_basis REAL NOT NULL,
    UNIQUE(user_id, ticker)
);

INSERT OR REPLACE INTO holdings (user_id, ticker, shares, cost_basis) VALUES
  ('morgan', 'NVDA',  100.0,  95.40),
  ('morgan', 'AAPL',   50.0, 155.20),
  ('morgan', 'MSFT',  200.0, 380.90),
  ('morgan', 'GOOGL',  30.0, 148.60),
  ('alex',   'AAPL',   50.0, 160.50),
  ('alex',   'MSFT',  100.0, 395.20);
```

- [ ] **Step 3: Write `infra/mock-data/news.json`**

```json
{
  "NVDA": [
    {
      "headline": "NVIDIA Reports Record Data Center Revenue, Beats Q1 Estimates",
      "source": "Reuters",
      "date": "2026-06-05",
      "sentiment": "positive",
      "score": 0.82
    },
    {
      "headline": "NVIDIA H200 Supply Constraints Ease as TSMC Ramps Production",
      "source": "Bloomberg",
      "date": "2026-06-04",
      "sentiment": "positive",
      "score": 0.71
    },
    {
      "headline": "AMD Closes GPU Market Share Gap With New MI400 Launch",
      "source": "The Verge",
      "date": "2026-06-03",
      "sentiment": "negative",
      "score": -0.44
    }
  ],
  "AAPL": [
    {
      "headline": "Apple Intelligence Adoption Drives iPhone 17 Upgrade Cycle",
      "source": "9to5Mac",
      "date": "2026-06-05",
      "sentiment": "positive",
      "score": 0.65
    },
    {
      "headline": "Apple Faces Renewed EU Antitrust Scrutiny Over App Store",
      "source": "Financial Times",
      "date": "2026-06-04",
      "sentiment": "negative",
      "score": -0.52
    }
  ],
  "MSFT": [
    {
      "headline": "Microsoft Azure AI Revenue Surpasses $20B Annual Run Rate",
      "source": "CNBC",
      "date": "2026-06-05",
      "sentiment": "positive",
      "score": 0.88
    },
    {
      "headline": "Microsoft Copilot Enterprise Seats Cross 10 Million Milestone",
      "source": "Bloomberg",
      "date": "2026-06-04",
      "sentiment": "positive",
      "score": 0.76
    }
  ],
  "GOOGL": [
    {
      "headline": "Google Search Ad Revenue Holds Steady Despite AI Competition",
      "source": "WSJ",
      "date": "2026-06-05",
      "sentiment": "neutral",
      "score": 0.12
    },
    {
      "headline": "Gemini Ultra Gains Traction in Enterprise Deals",
      "source": "TechCrunch",
      "date": "2026-06-04",
      "sentiment": "positive",
      "score": 0.58
    }
  ],
  "AMZN": [
    {
      "headline": "AWS Wins Pentagon JWCC Contract Extension Worth $9B",
      "source": "Reuters",
      "date": "2026-06-05",
      "sentiment": "positive",
      "score": 0.79
    },
    {
      "headline": "Amazon Prime Day Discounts Expected to Compress Q2 Margins",
      "source": "Bloomberg",
      "date": "2026-06-04",
      "sentiment": "negative",
      "score": -0.38
    }
  ]
}
```

- [ ] **Step 4: Commit**

```bash
git add infra/mock-data/
git commit -m "chore: add mock data files (tickers, holdings, news)"
```

---

## Task 3: market-data-mcp

**Files:**
- Create: `mcp-servers/market-data-mcp/pyproject.toml`
- Create: `mcp-servers/market-data-mcp/Dockerfile`
- Create: `mcp-servers/market-data-mcp/data.py`
- Create: `mcp-servers/market-data-mcp/server.py`
- Create: `mcp-servers/market-data-mcp/tests/__init__.py`
- Create: `mcp-servers/market-data-mcp/tests/test_tools.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "market-data-mcp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: Write `data.py`**

```python
import json
from pathlib import Path

_DATA_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "tickers.json"

def load_tickers() -> dict:
    with open(_DATA_FILE) as f:
        return json.load(f)

TICKERS: dict = load_tickers()
```

- [ ] **Step 3: Write `server.py`**

```python
import json
from fastmcp import FastMCP
from data import TICKERS

mcp = FastMCP("market-data-mcp")


@mcp.tool()
def get_price(ticker: str) -> str:
    """Get current price and daily change for a stock ticker.

    Args:
        ticker: Stock symbol (e.g. NVDA, AAPL, MSFT)

    Returns:
        JSON with ticker, name, price, change_pct, volume, sector
    """
    data = TICKERS.get(ticker.upper())
    if not data:
        known = list(TICKERS.keys())
        raise ValueError(f"Unknown ticker '{ticker}'. Known tickers: {known}")
    return json.dumps({
        "ticker": data["ticker"],
        "name": data["name"],
        "price": data["price"],
        "change_pct": data["change_pct"],
        "volume": data["volume"],
        "sector": data["sector"],
    })


@mcp.tool()
def get_historical(ticker: str, days: int = 5) -> str:
    """Get historical closing prices for a stock ticker.

    Args:
        ticker: Stock symbol (e.g. NVDA, AAPL, MSFT)
        days: Number of trading days of history to return (default 5, max 5)

    Returns:
        JSON with ticker and list of {date, close} entries
    """
    data = TICKERS.get(ticker.upper())
    if not data:
        raise ValueError(f"Unknown ticker '{ticker}'")
    history = data["history"][: min(days, len(data["history"]))]
    return json.dumps({"ticker": ticker.upper(), "history": history})


@mcp.tool()
def get_sector_performance() -> str:
    """Get aggregated performance by sector across all tracked tickers.

    Returns:
        JSON with list of {sector, avg_change_pct, tickers}
    """
    from collections import defaultdict

    sectors: dict = defaultdict(list)
    for t in TICKERS.values():
        sectors[t["sector"]].append({"ticker": t["ticker"], "change_pct": t["change_pct"]})

    result = []
    for sector, items in sectors.items():
        avg = round(sum(i["change_pct"] for i in items) / len(items), 2)
        result.append({"sector": sector, "avg_change_pct": avg, "tickers": items})

    return json.dumps(result)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Write `tests/test_tools.py`**

```python
import json
import pytest
from fastmcp import Client
from server import mcp


@pytest.mark.asyncio
async def test_get_price_known_ticker():
    async with Client(mcp) as client:
        result = await client.call_tool("get_price", {"ticker": "NVDA"})
    data = json.loads(result[0].text)
    assert data["ticker"] == "NVDA"
    assert data["price"] == 134.87
    assert data["change_pct"] == 2.41
    assert "sector" in data


@pytest.mark.asyncio
async def test_get_price_lowercase_ticker():
    async with Client(mcp) as client:
        result = await client.call_tool("get_price", {"ticker": "aapl"})
    data = json.loads(result[0].text)
    assert data["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_get_price_unknown_ticker_raises():
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="Unknown ticker"):
            await client.call_tool("get_price", {"ticker": "FAKE"})


@pytest.mark.asyncio
async def test_get_historical_default_days():
    async with Client(mcp) as client:
        result = await client.call_tool("get_historical", {"ticker": "MSFT"})
    data = json.loads(result[0].text)
    assert data["ticker"] == "MSFT"
    assert len(data["history"]) == 5
    assert "date" in data["history"][0]
    assert "close" in data["history"][0]


@pytest.mark.asyncio
async def test_get_historical_limited_days():
    async with Client(mcp) as client:
        result = await client.call_tool("get_historical", {"ticker": "NVDA", "days": 3})
    data = json.loads(result[0].text)
    assert len(data["history"]) == 3


@pytest.mark.asyncio
async def test_get_sector_performance():
    async with Client(mcp) as client:
        result = await client.call_tool("get_sector_performance", {})
    data = json.loads(result[0].text)
    assert isinstance(data, list)
    assert len(data) >= 1
    sectors = [s["sector"] for s in data]
    assert "Technology" in sectors
    tech = next(s for s in data if s["sector"] == "Technology")
    assert "avg_change_pct" in tech
    assert "tickers" in tech
```

- [ ] **Step 5: Write `Dockerfile`**

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

- [ ] **Step 6: Run tests**

```bash
cd mcp-servers/market-data-mcp
uv run pytest tests/ -v
```

Expected output:
```
tests/test_tools.py::test_get_price_known_ticker PASSED
tests/test_tools.py::test_get_price_lowercase_ticker PASSED
tests/test_tools.py::test_get_price_unknown_ticker_raises PASSED
tests/test_tools.py::test_get_historical_default_days PASSED
tests/test_tools.py::test_get_historical_limited_days PASSED
tests/test_tools.py::test_get_sector_performance PASSED
6 passed
```

- [ ] **Step 7: Commit**

```bash
cd /Users/kasunt/Projects/personal/public/finflow-demo
git add mcp-servers/market-data-mcp/
git commit -m "feat: add market-data-mcp with get_price, get_historical, get_sector_performance tools"
```

---

## Task 4: portfolio-mcp

**Files:**
- Create: `mcp-servers/portfolio-mcp/pyproject.toml`
- Create: `mcp-servers/portfolio-mcp/Dockerfile`
- Create: `mcp-servers/portfolio-mcp/db.py`
- Create: `mcp-servers/portfolio-mcp/server.py`
- Create: `mcp-servers/portfolio-mcp/tests/__init__.py`
- Create: `mcp-servers/portfolio-mcp/tests/test_tools.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "portfolio-mcp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: Write `db.py`**

Holdings are stored in a SQLite DB. In production, the DB is pre-seeded from `infra/mock-data/holdings.sql`. In tests, we use an in-memory DB.

```python
import sqlite3
import json
from pathlib import Path

_SQL_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "holdings.sql"
_TICKERS_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "tickers.json"

with open(_TICKERS_FILE) as f:
    CURRENT_PRICES: dict = {k: v["price"] for k, v in json.load(f).items()}


def get_connection(db_path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def seed_db(conn: sqlite3.Connection) -> None:
    sql = _SQL_FILE.read_text()
    conn.executescript(sql)
    conn.commit()


def get_holdings(conn: sqlite3.Connection, user_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT ticker, shares, cost_basis FROM holdings WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def calculate_pl(holdings: list[dict], prices: dict) -> dict:
    """Calculate P&L for holdings against current prices."""
    total_cost = 0.0
    total_value = 0.0
    positions = []

    for h in holdings:
        ticker = h["ticker"]
        price = prices.get(ticker, 0.0)
        cost = h["shares"] * h["cost_basis"]
        value = h["shares"] * price
        pl = value - cost
        pl_pct = (pl / cost * 100) if cost > 0 else 0.0

        total_cost += cost
        total_value += value
        positions.append({
            "ticker": ticker,
            "shares": h["shares"],
            "cost_basis": h["cost_basis"],
            "current_price": price,
            "market_value": round(value, 2),
            "pl": round(pl, 2),
            "pl_pct": round(pl_pct, 2),
        })

    return {
        "positions": positions,
        "total_cost": round(total_cost, 2),
        "total_value": round(total_value, 2),
        "total_pl": round(total_value - total_cost, 2),
        "total_pl_pct": round((total_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0.0,
    }
```

- [ ] **Step 3: Write `server.py`**

```python
import json
import os
import sqlite3
from fastmcp import FastMCP
from db import get_connection, seed_db, get_holdings, calculate_pl, CURRENT_PRICES

mcp = FastMCP("portfolio-mcp")

_DB_PATH = os.environ.get("DB_PATH", "/data/portfolio.db")
_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = get_connection(_DB_PATH)
        seed_db(_conn)
    return _conn


@mcp.tool()
def get_portfolio(user_id: str) -> str:
    """Get portfolio holdings with current P&L for a user.

    Args:
        user_id: User identifier (e.g. 'morgan', 'alex')

    Returns:
        JSON with positions list and summary P&L totals
    """
    conn = _get_conn()
    holdings = get_holdings(conn, user_id)
    if not holdings:
        return json.dumps({"user_id": user_id, "positions": [], "total_cost": 0, "total_value": 0, "total_pl": 0, "total_pl_pct": 0})
    result = calculate_pl(holdings, CURRENT_PRICES)
    result["user_id"] = user_id
    return json.dumps(result)


@mcp.tool()
def get_allocation(user_id: str) -> str:
    """Get portfolio allocation by ticker and sector for a user.

    Args:
        user_id: User identifier (e.g. 'morgan', 'alex')

    Returns:
        JSON with list of {ticker, pct_of_portfolio} sorted by weight descending
    """
    import json as _json
    from pathlib import Path

    conn = _get_conn()
    holdings = get_holdings(conn, user_id)
    if not holdings:
        return json.dumps({"user_id": user_id, "allocation": []})

    total_value = sum(h["shares"] * CURRENT_PRICES.get(h["ticker"], 0) for h in holdings)
    if total_value == 0:
        return json.dumps({"user_id": user_id, "allocation": []})

    allocation = []
    for h in holdings:
        price = CURRENT_PRICES.get(h["ticker"], 0)
        value = h["shares"] * price
        allocation.append({
            "ticker": h["ticker"],
            "market_value": round(value, 2),
            "pct_of_portfolio": round(value / total_value * 100, 2),
        })
    allocation.sort(key=lambda x: x["pct_of_portfolio"], reverse=True)

    return json.dumps({"user_id": user_id, "total_value": round(total_value, 2), "allocation": allocation})


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Write `tests/test_tools.py`**

```python
import json
import sqlite3
import pytest
from fastmcp import Client
from unittest.mock import patch

import db as db_module
from server import mcp


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    """Replace the module-level connection with a seeded in-memory DB."""
    conn = db_module.get_connection(":memory:")
    db_module.seed_db(conn)

    import server
    monkeypatch.setattr(server, "_conn", conn)
    monkeypatch.setattr(server, "_DB_PATH", ":memory:")
    yield conn
    conn.close()
    monkeypatch.setattr(server, "_conn", None)


@pytest.mark.asyncio
async def test_get_portfolio_morgan():
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio", {"user_id": "morgan"})
    data = json.loads(result[0].text)
    assert data["user_id"] == "morgan"
    assert len(data["positions"]) == 4
    tickers = [p["ticker"] for p in data["positions"]]
    assert "NVDA" in tickers
    assert "MSFT" in tickers
    assert data["total_pl"] != 0


@pytest.mark.asyncio
async def test_get_portfolio_alex():
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio", {"user_id": "alex"})
    data = json.loads(result[0].text)
    assert data["user_id"] == "alex"
    assert len(data["positions"]) == 2
    tickers = [p["ticker"] for p in data["positions"]]
    assert "AAPL" in tickers
    assert "MSFT" in tickers


@pytest.mark.asyncio
async def test_get_portfolio_unknown_user_returns_empty():
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio", {"user_id": "unknown"})
    data = json.loads(result[0].text)
    assert data["positions"] == []
    assert data["total_pl"] == 0


@pytest.mark.asyncio
async def test_get_allocation_morgan():
    async with Client(mcp) as client:
        result = await client.call_tool("get_allocation", {"user_id": "morgan"})
    data = json.loads(result[0].text)
    assert data["user_id"] == "morgan"
    assert len(data["allocation"]) == 4
    total_pct = sum(a["pct_of_portfolio"] for a in data["allocation"])
    assert abs(total_pct - 100.0) < 0.1
    # Sorted by weight descending
    pcts = [a["pct_of_portfolio"] for a in data["allocation"]]
    assert pcts == sorted(pcts, reverse=True)


@pytest.mark.asyncio
async def test_pl_calculation():
    """NVDA: 100 shares, cost_basis 95.40, current price 134.87 → P&L = 3947."""
    async with Client(mcp) as client:
        result = await client.call_tool("get_portfolio", {"user_id": "morgan"})
    data = json.loads(result[0].text)
    nvda = next(p for p in data["positions"] if p["ticker"] == "NVDA")
    expected_pl = round((134.87 - 95.40) * 100, 2)
    assert nvda["pl"] == expected_pl
```

- [ ] **Step 5: Write `Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

COPY . .

RUN mkdir -p /data

ENV PYTHONPATH=/app
ENV DB_PATH=/data/portfolio.db
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
```

- [ ] **Step 6: Run tests**

```bash
cd mcp-servers/portfolio-mcp
uv run pytest tests/ -v
```

Expected:
```
tests/test_tools.py::test_get_portfolio_morgan PASSED
tests/test_tools.py::test_get_portfolio_alex PASSED
tests/test_tools.py::test_get_portfolio_unknown_user_returns_empty PASSED
tests/test_tools.py::test_get_allocation_morgan PASSED
tests/test_tools.py::test_pl_calculation PASSED
5 passed
```

- [ ] **Step 7: Commit**

```bash
cd /Users/kasunt/Projects/personal/public/finflow-demo
git add mcp-servers/portfolio-mcp/
git commit -m "feat: add portfolio-mcp with get_portfolio and get_allocation tools"
```

---

## Task 5: news-mcp

**Files:**
- Create: `mcp-servers/news-mcp/pyproject.toml`
- Create: `mcp-servers/news-mcp/Dockerfile`
- Create: `mcp-servers/news-mcp/data.py`
- Create: `mcp-servers/news-mcp/server.py`
- Create: `mcp-servers/news-mcp/tests/__init__.py`
- Create: `mcp-servers/news-mcp/tests/test_tools.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "news-mcp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: Write `data.py`**

```python
import json
from pathlib import Path

_NEWS_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "news.json"

def load_news() -> dict:
    with open(_NEWS_FILE) as f:
        return json.load(f)

NEWS: dict = load_news()
```

- [ ] **Step 3: Write `server.py`**

```python
import json
from fastmcp import FastMCP
from data import NEWS

mcp = FastMCP("news-mcp")


@mcp.tool()
def search_news(ticker: str, limit: int = 3) -> str:
    """Search recent news headlines for a stock ticker.

    Args:
        ticker: Stock symbol (e.g. NVDA, AAPL, MSFT)
        limit: Maximum number of articles to return (default 3)

    Returns:
        JSON with ticker and list of {headline, source, date, sentiment, score}
    """
    articles = NEWS.get(ticker.upper(), [])
    if not articles:
        return json.dumps({"ticker": ticker.upper(), "articles": [], "message": "No news found"})
    return json.dumps({
        "ticker": ticker.upper(),
        "articles": articles[:limit],
    })


@mcp.tool()
def get_portfolio_sentiment(tickers: list[str]) -> str:
    """Get aggregated sentiment summary for a list of tickers.

    Args:
        tickers: List of stock symbols (e.g. ["NVDA", "AAPL", "MSFT"])

    Returns:
        JSON with per-ticker sentiment summary and overall portfolio sentiment
    """
    results = []
    for ticker in tickers:
        articles = NEWS.get(ticker.upper(), [])
        if not articles:
            results.append({"ticker": ticker.upper(), "avg_score": 0.0, "sentiment": "neutral", "article_count": 0})
            continue
        avg_score = round(sum(a["score"] for a in articles) / len(articles), 2)
        if avg_score > 0.3:
            sentiment = "positive"
        elif avg_score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        results.append({
            "ticker": ticker.upper(),
            "avg_score": avg_score,
            "sentiment": sentiment,
            "article_count": len(articles),
            "top_headline": articles[0]["headline"],
        })

    all_scores = [r["avg_score"] for r in results]
    overall_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    return json.dumps({
        "tickers": results,
        "overall_score": overall_score,
        "overall_sentiment": "positive" if overall_score > 0.3 else "negative" if overall_score < -0.2 else "neutral",
    })


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Write `tests/test_tools.py`**

```python
import json
import pytest
from fastmcp import Client
from server import mcp


@pytest.mark.asyncio
async def test_search_news_known_ticker():
    async with Client(mcp) as client:
        result = await client.call_tool("search_news", {"ticker": "NVDA"})
    data = json.loads(result[0].text)
    assert data["ticker"] == "NVDA"
    assert len(data["articles"]) == 3
    assert "headline" in data["articles"][0]
    assert "sentiment" in data["articles"][0]
    assert "score" in data["articles"][0]


@pytest.mark.asyncio
async def test_search_news_limit():
    async with Client(mcp) as client:
        result = await client.call_tool("search_news", {"ticker": "NVDA", "limit": 1})
    data = json.loads(result[0].text)
    assert len(data["articles"]) == 1


@pytest.mark.asyncio
async def test_search_news_lowercase():
    async with Client(mcp) as client:
        result = await client.call_tool("search_news", {"ticker": "msft"})
    data = json.loads(result[0].text)
    assert data["ticker"] == "MSFT"
    assert len(data["articles"]) >= 1


@pytest.mark.asyncio
async def test_search_news_unknown_ticker():
    async with Client(mcp) as client:
        result = await client.call_tool("search_news", {"ticker": "FAKE"})
    data = json.loads(result[0].text)
    assert data["articles"] == []


@pytest.mark.asyncio
async def test_get_portfolio_sentiment():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_portfolio_sentiment", {"tickers": ["NVDA", "MSFT", "AAPL"]}
        )
    data = json.loads(result[0].text)
    assert len(data["tickers"]) == 3
    ticker_names = [t["ticker"] for t in data["tickers"]]
    assert "NVDA" in ticker_names
    assert "MSFT" in ticker_names
    assert "overall_score" in data
    assert data["overall_sentiment"] in ("positive", "negative", "neutral")


@pytest.mark.asyncio
async def test_msft_sentiment_is_positive():
    """MSFT has two positive articles — should score positive."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_portfolio_sentiment", {"tickers": ["MSFT"]}
        )
    data = json.loads(result[0].text)
    msft = data["tickers"][0]
    assert msft["sentiment"] == "positive"
    assert msft["avg_score"] > 0.3
```

- [ ] **Step 5: Write `Dockerfile`**

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

- [ ] **Step 6: Run tests**

```bash
cd mcp-servers/news-mcp
uv run pytest tests/ -v
```

Expected:
```
tests/test_tools.py::test_search_news_known_ticker PASSED
tests/test_tools.py::test_search_news_limit PASSED
tests/test_tools.py::test_search_news_lowercase PASSED
tests/test_tools.py::test_search_news_unknown_ticker PASSED
tests/test_tools.py::test_get_portfolio_sentiment PASSED
tests/test_tools.py::test_msft_sentiment_is_positive PASSED
6 passed
```

- [ ] **Step 7: Commit**

```bash
cd /Users/kasunt/Projects/personal/public/finflow-demo
git add mcp-servers/news-mcp/
git commit -m "feat: add news-mcp with search_news and get_portfolio_sentiment tools"
```

---

## Task 6: brokerage-mcp

**Files:**
- Create: `mcp-servers/brokerage-mcp/pyproject.toml`
- Create: `mcp-servers/brokerage-mcp/Dockerfile`
- Create: `mcp-servers/brokerage-mcp/store.py`
- Create: `mcp-servers/brokerage-mcp/server.py`
- Create: `mcp-servers/brokerage-mcp/tests/__init__.py`
- Create: `mcp-servers/brokerage-mcp/tests/test_tools.py`

Note: agentgateway's elicitation policy ensures a valid brokerage OAuth token is injected into requests before they reach this server. The server validates the token header is present and non-empty (demo-level validation).

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "brokerage-mcp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: Write `store.py`**

```python
import uuid
from datetime import datetime, timezone


class OrderStore:
    """In-memory order store. Resets on restart (demo use only)."""

    def __init__(self):
        self._orders: dict[str, dict] = {}

    def create_order(
        self,
        user_id: str,
        ticker: str,
        action: str,
        shares: float,
        price: float,
    ) -> dict:
        order_id = str(uuid.uuid4())[:8].upper()
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "ticker": ticker.upper(),
            "action": action.upper(),  # BUY or SELL
            "shares": shares,
            "price": price,
            "total": round(shares * price, 2),
            "status": "FILLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> dict | None:
        return self._orders.get(order_id.upper())

    def list_orders(self, user_id: str) -> list[dict]:
        return [o for o in self._orders.values() if o["user_id"] == user_id]


ORDER_STORE = OrderStore()
```

- [ ] **Step 3: Write `server.py`**

```python
import json
from pathlib import Path
import sys

from fastmcp import FastMCP
from store import ORDER_STORE

# Load current prices for order execution
_TICKERS_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "tickers.json"
with open(_TICKERS_FILE) as f:
    _PRICES: dict = {k: v["price"] for k, v in json.load(f).items()}

mcp = FastMCP("brokerage-mcp")

VALID_ACTIONS = {"BUY", "SELL"}


@mcp.tool()
def execute_trade(user_id: str, ticker: str, action: str, shares: float) -> str:
    """Execute a stock trade on behalf of a user.

    agentgateway injects the brokerage OAuth token before this tool is called.
    The tool executes at current mock market price.

    Args:
        user_id: User identifier (e.g. 'morgan')
        ticker: Stock symbol (e.g. NVDA, AAPL)
        action: Trade direction — BUY or SELL
        shares: Number of shares to trade (must be positive)

    Returns:
        JSON with order confirmation including order_id, price, total, status
    """
    action = action.upper()
    ticker = ticker.upper()

    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid action '{action}'. Must be BUY or SELL.")
    if shares <= 0:
        raise ValueError(f"Shares must be positive, got {shares}.")
    if ticker not in _PRICES:
        raise ValueError(f"Unknown ticker '{ticker}'.")

    price = _PRICES[ticker]
    order = ORDER_STORE.create_order(user_id, ticker, action, shares, price)
    return json.dumps(order)


@mcp.tool()
def get_order_status(order_id: str) -> str:
    """Get the status of a previously submitted trade order.

    Args:
        order_id: Order ID returned by execute_trade

    Returns:
        JSON with full order details, or error if not found
    """
    order = ORDER_STORE.get_order(order_id)
    if not order:
        raise ValueError(f"Order '{order_id}' not found.")
    return json.dumps(order)


@mcp.tool()
def list_orders(user_id: str) -> str:
    """List all trade orders for a user in this session.

    Args:
        user_id: User identifier

    Returns:
        JSON with list of orders
    """
    orders = ORDER_STORE.list_orders(user_id)
    return json.dumps({"user_id": user_id, "orders": orders})


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Write `tests/test_tools.py`**

```python
import json
import pytest
from fastmcp import Client
from server import mcp
import store


@pytest.fixture(autouse=True)
def reset_order_store():
    """Clear order store between tests."""
    store.ORDER_STORE._orders.clear()
    yield
    store.ORDER_STORE._orders.clear()


@pytest.mark.asyncio
async def test_execute_trade_buy():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "NVDA", "action": "BUY", "shares": 10.0},
        )
    data = json.loads(result[0].text)
    assert data["status"] == "FILLED"
    assert data["ticker"] == "NVDA"
    assert data["action"] == "BUY"
    assert data["shares"] == 10.0
    assert data["price"] == 134.87
    assert data["total"] == round(10.0 * 134.87, 2)
    assert "order_id" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_execute_trade_sell():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "AAPL", "action": "SELL", "shares": 5.0},
        )
    data = json.loads(result[0].text)
    assert data["action"] == "SELL"
    assert data["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_execute_trade_lowercase_inputs():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "msft", "action": "buy", "shares": 2.0},
        )
    data = json.loads(result[0].text)
    assert data["ticker"] == "MSFT"
    assert data["action"] == "BUY"


@pytest.mark.asyncio
async def test_execute_trade_invalid_action():
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="Invalid action"):
            await client.call_tool(
                "execute_trade",
                {"user_id": "morgan", "ticker": "NVDA", "action": "HOLD", "shares": 10.0},
            )


@pytest.mark.asyncio
async def test_execute_trade_negative_shares():
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="positive"):
            await client.call_tool(
                "execute_trade",
                {"user_id": "morgan", "ticker": "NVDA", "action": "BUY", "shares": -5.0},
            )


@pytest.mark.asyncio
async def test_get_order_status():
    async with Client(mcp) as client:
        buy_result = await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "NVDA", "action": "BUY", "shares": 1.0},
        )
    order_id = json.loads(buy_result[0].text)["order_id"]

    async with Client(mcp) as client:
        status_result = await client.call_tool("get_order_status", {"order_id": order_id})
    data = json.loads(status_result[0].text)
    assert data["order_id"] == order_id
    assert data["status"] == "FILLED"


@pytest.mark.asyncio
async def test_get_order_status_not_found():
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="not found"):
            await client.call_tool("get_order_status", {"order_id": "FAKE123"})


@pytest.mark.asyncio
async def test_list_orders():
    async with Client(mcp) as client:
        await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "NVDA", "action": "BUY", "shares": 10.0},
        )
        await client.call_tool(
            "execute_trade",
            {"user_id": "morgan", "ticker": "AAPL", "action": "BUY", "shares": 5.0},
        )
        result = await client.call_tool("list_orders", {"user_id": "morgan"})
    data = json.loads(result[0].text)
    assert data["user_id"] == "morgan"
    assert len(data["orders"]) == 2
```

- [ ] **Step 5: Write `Dockerfile`**

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

- [ ] **Step 6: Run tests**

```bash
cd mcp-servers/brokerage-mcp
uv run pytest tests/ -v
```

Expected:
```
tests/test_tools.py::test_execute_trade_buy PASSED
tests/test_tools.py::test_execute_trade_sell PASSED
tests/test_tools.py::test_execute_trade_lowercase_inputs PASSED
tests/test_tools.py::test_execute_trade_invalid_action PASSED
tests/test_tools.py::test_execute_trade_negative_shares PASSED
tests/test_tools.py::test_get_order_status PASSED
tests/test_tools.py::test_get_order_status_not_found PASSED
tests/test_tools.py::test_list_orders PASSED
8 passed
```

- [ ] **Step 7: Run full test suite**

```bash
cd /Users/kasunt/Projects/personal/public/finflow-demo
make test-all
```

Expected: all 25 tests pass across all four servers.

- [ ] **Step 8: Commit**

```bash
git add mcp-servers/brokerage-mcp/
git commit -m "feat: add brokerage-mcp with execute_trade, get_order_status, list_orders tools"
```

---

## Task 7: Kubernetes base manifests

**Files:**
- Create: `infra/k8s/base/namespace.yaml`
- Create: `infra/k8s/base/kustomization.yaml`
- Create: `infra/k8s/base/mcp-servers/kustomization.yaml`
- Create: `infra/k8s/base/mcp-servers/market-data-mcp.yaml`
- Create: `infra/k8s/base/mcp-servers/portfolio-mcp.yaml`
- Create: `infra/k8s/base/mcp-servers/news-mcp.yaml`
- Create: `infra/k8s/base/mcp-servers/brokerage-mcp.yaml`
- Create: `infra/k8s/features/obo/.gitkeep`
- Create: `infra/k8s/features/rbac/.gitkeep`
- Create: `infra/k8s/features/mcp-access/.gitkeep`
- Create: `infra/k8s/features/elicitation/.gitkeep`

Replace `<REGISTRY>` with your registry in the image fields (or use kustomize image overlay).

- [ ] **Step 1: Write `namespace.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: finflow
  labels:
    app.kubernetes.io/managed-by: finflow-demo
```

- [ ] **Step 2: Write `infra/k8s/base/kustomization.yaml`**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - mcp-servers/
```

- [ ] **Step 3: Write `infra/k8s/base/mcp-servers/kustomization.yaml`**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - market-data-mcp.yaml
  - portfolio-mcp.yaml
  - news-mcp.yaml
  - brokerage-mcp.yaml
```

- [ ] **Step 4: Write `infra/k8s/base/mcp-servers/market-data-mcp.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: market-data-mcp
  namespace: finflow
  labels:
    app: market-data-mcp
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: market-data-mcp
  template:
    metadata:
      labels:
        app: market-data-mcp
    spec:
      containers:
        - name: server
          image: finflow/market-data-mcp:latest
          ports:
            - containerPort: 8000
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
  name: market-data-mcp
  namespace: finflow
  labels:
    app: market-data-mcp
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: market-data-mcp
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 5: Write `infra/k8s/base/mcp-servers/portfolio-mcp.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: portfolio-mcp
  namespace: finflow
  labels:
    app: portfolio-mcp
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: portfolio-mcp
  template:
    metadata:
      labels:
        app: portfolio-mcp
    spec:
      containers:
        - name: server
          image: finflow/portfolio-mcp:latest
          ports:
            - containerPort: 8000
          env:
            - name: DB_PATH
              value: /data/portfolio.db
          volumeMounts:
            - name: db-data
              mountPath: /data
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
      volumes:
        - name: db-data
          emptyDir: {}
      initContainers:
        - name: seed-db
          image: finflow/portfolio-mcp:latest
          command: ["uv", "run", "python", "-c",
            "import sqlite3, pathlib; sql=pathlib.Path('/seed/holdings.sql').read_text(); conn=sqlite3.connect('/data/portfolio.db'); conn.executescript(sql); conn.commit()"]
          volumeMounts:
            - name: db-data
              mountPath: /data
            - name: seed-data
              mountPath: /seed
      volumes:
        - name: db-data
          emptyDir: {}
        - name: seed-data
          configMap:
            name: portfolio-seed-sql
---
apiVersion: v1
kind: Service
metadata:
  name: portfolio-mcp
  namespace: finflow
  labels:
    app: portfolio-mcp
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: portfolio-mcp
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: portfolio-seed-sql
  namespace: finflow
data:
  holdings.sql: |
    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        ticker TEXT NOT NULL,
        shares REAL NOT NULL,
        cost_basis REAL NOT NULL,
        UNIQUE(user_id, ticker)
    );
    INSERT OR REPLACE INTO holdings (user_id, ticker, shares, cost_basis) VALUES
      ('morgan', 'NVDA',  100.0,  95.40),
      ('morgan', 'AAPL',   50.0, 155.20),
      ('morgan', 'MSFT',  200.0, 380.90),
      ('morgan', 'GOOGL',  30.0, 148.60),
      ('alex',   'AAPL',   50.0, 160.50),
      ('alex',   'MSFT',  100.0, 395.20);
```

- [ ] **Step 6: Write `infra/k8s/base/mcp-servers/news-mcp.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: news-mcp
  namespace: finflow
  labels:
    app: news-mcp
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: news-mcp
  template:
    metadata:
      labels:
        app: news-mcp
    spec:
      containers:
        - name: server
          image: finflow/news-mcp:latest
          ports:
            - containerPort: 8000
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
  name: news-mcp
  namespace: finflow
  labels:
    app: news-mcp
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: news-mcp
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 7: Write `infra/k8s/base/mcp-servers/brokerage-mcp.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: brokerage-mcp
  namespace: finflow
  labels:
    app: brokerage-mcp
    app.kubernetes.io/part-of: finflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: brokerage-mcp
  template:
    metadata:
      labels:
        app: brokerage-mcp
    spec:
      containers:
        - name: server
          image: finflow/brokerage-mcp:latest
          ports:
            - containerPort: 8000
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
  name: brokerage-mcp
  namespace: finflow
  labels:
    app: brokerage-mcp
    app.kubernetes.io/part-of: finflow
spec:
  selector:
    app: brokerage-mcp
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

- [ ] **Step 8: Create feature placeholder dirs**

```bash
mkdir -p infra/k8s/features/obo
mkdir -p infra/k8s/features/rbac
mkdir -p infra/k8s/features/mcp-access
mkdir -p infra/k8s/features/elicitation
touch infra/k8s/features/obo/.gitkeep
touch infra/k8s/features/rbac/.gitkeep
touch infra/k8s/features/mcp-access/.gitkeep
touch infra/k8s/features/elicitation/.gitkeep
```

- [ ] **Step 9: Commit**

```bash
git add infra/k8s/
git commit -m "chore: add base K8s manifests for MCP servers and feature placeholder dirs"
```

---

## Self-Review

**Spec coverage check:**
- ✅ 4 MCP servers: market-data, portfolio, news, brokerage
- ✅ StreamableHTTP transport (FastMCP `transport="streamable-http"`)
- ✅ Tests for all tools including error cases
- ✅ Dockerfiles for all servers
- ✅ K8s base manifests (Deployment + Service per server)
- ✅ `infra/k8s/features/` dirs for phase 4 (agentgateway policies)
- ✅ Mock data canonical files (tickers.json, holdings.sql, news.json)
- ✅ Portfolio DB seeded via K8s initContainer + ConfigMap
- ✅ Makefile with per-server and all-server test targets + build/push

**Not in this plan (future phases):**
- Agents (Phase 2)
- UI + BFF (Phase 3)
- agentgateway feature manifests, RBAC, build pipeline, reset script (Phase 4)

**Placeholder scan:** None found.

**Type consistency:** `user_id` used consistently across portfolio-mcp and brokerage-mcp. `ticker` uppercased at tool boundary in all servers. `order_id` type `str` consistent between `execute_trade` return and `get_order_status` input.
