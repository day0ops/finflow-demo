# FinFlow Demo

[![CI](https://github.com/day0ops/finflow-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/day0ops/finflow-demo/actions/workflows/ci.yml)
[![Release](https://github.com/day0ops/finflow-demo/actions/workflows/release.yml/badge.svg)](https://github.com/day0ops/finflow-demo/actions/workflows/release.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Multi-agent financial portfolio assistant demonstrating the Solo.io agentic product suite: agentgateway, agentregistry, and Istio ambient mesh.

## Architecture

```
Browser → AgentGateway (auth, rate-limit, guardrails, RBAC)
              └── BFF (Next.js + FastAPI)
                    └── Orchestrator
                          ├── Market Data Agent   (Google ADK + MCP)
                          ├── Portfolio Agent     (Google ADK + MCP)
                          ├── News Sentiment Agent (Anthropic SDK + MCP)
                          └── Trade Execution Agent (Anthropic SDK + MCP)
```

## Repository Structure

| Directory | Description |
|---|---|
| `agents/` | Agent implementations (orchestrator, market-data, portfolio, news-sentiment, trade-execution) |
| `mcp-servers/` | FastMCP tool servers (market-data, portfolio, news, brokerage) |
| `bff/` | Backend-for-frontend (FastAPI) — proxies requests, handles auth |
| `ui/` | Next.js frontend |
| `infra/k8s/` | Kubernetes manifests (base + feature overlays) |
| `infra/agentregistry/` | AgentRegistry catalog and AgentCore deployment manifests |

## Prerequisites

- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- [Bun](https://bun.sh/) 1.x
- Docker with Buildx
- kubectl

## Quick Start

```bash
# Run all tests
make test-all

# Build all images
make build REGISTRY=<your-registry>

# Deploy to Kubernetes
kubectl apply -k infra/k8s/base/
```

## Development

```bash
# MCP server tests
make test-mcp

# Agent tests
make test-agents

# BFF tests
make test-bff

# UI tests
make test-ui
```

## Release

Images are published to Google Artifact Registry on semver tags:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Requires `WORKLOAD_IDENTITY_PROVIDER` and `SERVICE_ACCOUNT` repository secrets configured for Workload Identity Federation.

## License

[Apache 2.0](LICENSE)
