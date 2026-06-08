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

# ── BFF tests ────────────────────────────────────────────────────────────────────
test-bff:
	cd bff && uv run pytest tests/ -v

# ── UI tests ──────────────────────────────────────────────────────────────────────
test-ui:
	cd ui && bun run test

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
test-all: test-mcp test-agents test-bff test-ui

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
	docker build -t $(REGISTRY)/finflow/bff:$(TAG) bff
	docker build -t $(REGISTRY)/finflow/ui:$(TAG) ui

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
	docker push $(REGISTRY)/finflow/bff:$(TAG)
	docker push $(REGISTRY)/finflow/ui:$(TAG)
