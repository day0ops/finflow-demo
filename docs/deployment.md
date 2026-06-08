# FinFlow Deployment Guide

This guide covers deploying FinFlow into an environment that already has **Istio Ambient**, **AgentGateway (Enterprise)**, and **AgentRegistry** running.

## Do you need Kagent?

**No.** Kagent is a Kubernetes-native agent lifecycle controller for agents defined as CRDs. FinFlow agents are plain FastAPI containers deployed as standard `Deployment` + `Service` resources. AgentGateway routes to them via `HTTPRoute`; AgentRegistry catalogs them via `arctl`. Kagent adds no value here and is not required.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Kubernetes cluster | ≥1.28 | EKS, GKE, or local kind/k3s |
| Istio Ambient | ≥1.23 | ztunnel daemonset running |
| AgentGateway Enterprise | v2026.5.2 | Helm charts installed |
| AgentRegistry Enterprise | v2026.5.4 | Helm charts installed |
| Container registry | any | `localhost:5000` for local |
| `kubectl`, `helm`, `arctl` | latest | CLI tools on PATH |

If AgentGateway or AgentRegistry are **not yet installed**, see the sections below before proceeding to FinFlow deployment.

---

## 1. Install AgentGateway (if not already running)

```bash
# Gateway API CRDs (standard channel)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.0/standard-install.yaml

export AGENTGATEWAY_LICENSE_KEY=<your-license-key>

# CRDs chart
helm upgrade -i enterprise-agentgateway-crds \
  oci://us-docker.pkg.dev/solo-public/enterprise-agentgateway/charts/enterprise-agentgateway-crds \
  --create-namespace \
  --namespace agentgateway-system \
  --version v2026.5.2

# Control plane
helm upgrade -i enterprise-agentgateway \
  oci://us-docker.pkg.dev/solo-public/enterprise-agentgateway/charts/enterprise-agentgateway \
  --namespace agentgateway-system \
  --version v2026.5.2 \
  --set-string licensing.licenseKey=${AGENTGATEWAY_LICENSE_KEY}

kubectl -n agentgateway-system rollout status deployment/enterprise-agentgateway
```

Expected pods after install:

```
enterprise-agentgateway-<hash>   1/1   Running   # control plane
```

The data-plane proxy pods (`agentgateway-proxy`, `ext-auth-service`, `rate-limiter`, `ext-cache`) spin up when you apply the `Gateway` resource in step 4.

---

## 2. Install AgentRegistry (if not already running)

```bash
# Demo mode (no external OIDC) — suitable for development/demo
helm upgrade --install agentregistry \
  oci://us-docker.pkg.dev/solo-public/agentregistry-enterprise/helm/agentregistry-enterprise \
  --version 2026.5.4 \
  --namespace agentregistry-system \
  --create-namespace \
  --set oidc.demoAuthEnabled=true

kubectl -n agentregistry-system rollout status deployment/agentregistry-enterprise-server
```

For production with OIDC, replace `--set oidc.demoAuthEnabled=true` with your provider values:

```bash
  --set oidc.issuer=$KEYCLOAK_ISSUER \
  --set oidc.clientId=ar-backend \
  --set oidc.clientSecret=$AR_BACKEND_SECRET \
  --set oidc.publicClientId=ar-ui \
  --set oidc.roleClaim=Groups \
  --set oidc.superuserRole=admins
```

---

## 3. Build and Push FinFlow Images

Set your registry prefix:

```bash
export REGISTRY=<your-registry>   # e.g. localhost:5000 or ghcr.io/org
export TAG=latest
```

Build all images:

```bash
make build REGISTRY=$REGISTRY TAG=$TAG
```

Push:

```bash
make push REGISTRY=$REGISTRY TAG=$TAG
```

---

## 4. Deploy FinFlow to Kubernetes

### 4a. Create namespace and enroll in Ambient mesh

```bash
kubectl create namespace finflow

# Enroll in Istio Ambient (L4 mTLS via ztunnel — no pod restarts needed)
kubectl label namespace finflow istio.io/dataplane-mode=ambient

# Verify enrollment
kubectl get ns finflow -L istio.io/dataplane-mode
```

### 4b. Apply k8s manifests

Update image references in `infra/k8s/base/bff.yaml` and `infra/k8s/base/ui.yaml` to match your registry, then apply:

```bash
# Set the registry in kustomization (or patch directly)
cd infra/k8s/base

kubectl apply -k . -n finflow
```

Verify all pods are running:

```bash
kubectl -n finflow get pods
# Expected:
# bff-<hash>   1/1   Running
# ui-<hash>    1/1   Running
```

The orchestrator and MCP servers are separate services. Apply their manifests (if present) or deploy them manually:

```bash
kubectl -n finflow apply -f infra/k8s/agents/   # if you have agent manifests
```

### 4c. Deploy the AgentGateway data plane (Gateway resource)

Apply the `Gateway` resource to spin up the proxy:

```yaml
# infra/k8s/agentgateway/gateway.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: agentgateway-proxy
  namespace: agentgateway-system
spec:
  gatewayClassName: enterprise-agentgateway
  listeners:
  - protocol: HTTP
    port: 80
    name: http
    allowedRoutes:
      namespaces:
        from: All
```

```bash
kubectl apply -f infra/k8s/agentgateway/gateway.yaml

# Wait for the proxy pods to be ready
kubectl -n agentgateway-system rollout status deployment/agentgateway-proxy
```

### 4d. Configure HTTPRoutes to FinFlow services

Create routes for each service. The orchestrator is the primary entry point; the BFF and UI are internal:

```yaml
# infra/k8s/agentgateway/httproutes.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: finflow-orchestrator
  namespace: finflow
spec:
  parentRefs:
  - name: agentgateway-proxy
    namespace: agentgateway-system
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /orchestrator
    backendRefs:
    - name: finflow-orchestrator
      port: 8000
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: finflow-bff
  namespace: finflow
spec:
  parentRefs:
  - name: agentgateway-proxy
    namespace: agentgateway-system
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /bff
    backendRefs:
    - name: finflow-bff
      port: 8001
```

```bash
kubectl apply -f infra/k8s/agentgateway/httproutes.yaml
```

Get the gateway external address:

```bash
kubectl -n agentgateway-system get svc agentgateway-proxy
# Note the EXTERNAL-IP or LoadBalancer hostname
export GATEWAY_URL=http://<EXTERNAL-IP>
```

---

## 5. Register FinFlow Agents in AgentRegistry

### 5a. Install the arctl CLI

```bash
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')

gh release download v2026.5.4 \
  --repo solo-io/agentregistry-enterprise \
  --pattern "arctl-${OS}-${ARCH}" \
  --output arctl
chmod +x arctl
sudo mv arctl /usr/local/bin/arctl
```

### 5b. Connect arctl to the registry

```bash
kubectl -n agentregistry-system port-forward svc/agentregistry-enterprise-server 12121:12121 &

export ARCTL_API_BASE_URL=http://localhost:12121
# In demo auth mode, no token is needed. For OIDC: export ARCTL_API_TOKEN=<bearer-token>
```

### 5c. Register each agent

Create an agent manifest for each service and register it. Example for the orchestrator:

```bash
arctl init agent finflow-orchestrator
```

Edit the generated `finflow-orchestrator/agent.yaml` to reflect the service endpoint, then register:

```bash
arctl apply -f finflow-orchestrator/agent.yaml
```

Repeat for market-data, portfolio, news-sentiment, and trade-execution agents. Verify registrations:

```bash
arctl get agents
```

AgentRegistry also auto-discovers Kubernetes workloads connected to its runtime. Running workloads in the `finflow` namespace may appear automatically if the AgentRegistry has a Kubernetes runtime connected.

> **Agent card frameworks:** The `"framework"` field in each agent's `/.well-known/agent.json` card reflects the actual LLM framework used: `google-adk` for market-data and portfolio agents, `anthropic-sdk` for news-sentiment and trade-execution, and `custom` for the orchestrator (which is a pure HTTP dispatcher with no LLM framework).

---

## 6. Host Agents on AgentCore via AgentRegistry

This section covers deploying FinFlow agents to **Amazon Bedrock AgentCore** using the AgentRegistry catalog and deployment manifests in `infra/agentregistry/`.

> **Note:** Each agent has two entry points:
> - `server.py` — FastAPI server for local development and Kubernetes deployment
> - `main.py` — AgentCore entry point using `BedrockAgentCoreApp`

### Prerequisites

- AgentCore runtime registered in AgentRegistry:
  ```bash
  arctl get runtimes
  # Expected output includes:
  # agentcore   BedrockAgentCore
  ```
- AWS credentials configured with permissions to deploy to Bedrock AgentCore
- VPC subnet and security group IDs for AgentCore network isolation

### Step 1 — Update catalog manifests with your registry and repo

Edit each `infra/agentregistry/agents/<agent>.yaml` to replace:
- `<YOUR_ORG>` in `spec.source.repository.url` with your GitHub organization/user
- `localhost:5000` in `spec.source.image` with your actual container registry

### Step 2 — Publish each agent to the catalog

```bash
arctl apply -f infra/agentregistry/agents/market-data.yaml
arctl apply -f infra/agentregistry/agents/portfolio.yaml
arctl apply -f infra/agentregistry/agents/news-sentiment.yaml
arctl apply -f infra/agentregistry/agents/trade-execution.yaml
arctl apply -f infra/agentregistry/agents/orchestrator.yaml

# Verify
arctl get agents
```

### Step 3 — Set environment variables

```bash
export AWS_REGION=us-east-1          # your AWS region
export SUBNET_ID=subnet-xxxxxxxx     # VPC subnet for AgentCore
export SG_ID=sg-xxxxxxxx             # security group for AgentCore
export AGENTGATEWAY_HOST=<agentgateway-external-ip-or-hostname>
```

### Step 4 — Deploy each agent to AgentCore

```bash
envsubst < infra/agentregistry/deployments/market-data.yaml    | arctl apply -f -
envsubst < infra/agentregistry/deployments/portfolio.yaml      | arctl apply -f -
envsubst < infra/agentregistry/deployments/news-sentiment.yaml | arctl apply -f -
envsubst < infra/agentregistry/deployments/trade-execution.yaml| arctl apply -f -
envsubst < infra/agentregistry/deployments/orchestrator.yaml   | arctl apply -f -
```

Alternatively, edit the YAML files directly to substitute the placeholder values before running `arctl apply`.

### Step 5 — Monitor deployments

In the AgentRegistry UI, navigate to the **Instances** view to monitor deployment status. Each agent should transition from `Pending` → `Running`.

### Networking note

The orchestrator's `main.py` dispatches to sub-agents via env vars (`MARKET_DATA_AGENT_URL` etc.). When deployed to AgentCore, these are set to AgentGateway routes (see `infra/agentregistry/deployments/orchestrator.yaml`). The AgentCore VPC and the Kubernetes cluster running AgentGateway must share a network path (VPC peering, Transit Gateway, or same VPC).

---

## 7. Verify End-to-End

```bash
# Health check — BFF
curl $GATEWAY_URL/bff/health

# Tickers
curl $GATEWAY_URL/bff/api/tickers

# Chat (orchestrator via BFF)
curl -X POST $GATEWAY_URL/bff/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me a portfolio briefing", "session_id": "test-001"}'
```

Open the UI (port-forward or LoadBalancer):

```bash
kubectl -n finflow port-forward svc/finflow-ui 3000:3000
# Visit http://localhost:3000
```

---

## Optional: L7 Policies via Waypoint

The Ambient mesh provides L4 mTLS by default. If you need L7 policies (JWT validation, header-based authorization, fine-grained RBAC), deploy a waypoint proxy for the `finflow` namespace:

```bash
istioctl waypoint apply --namespace finflow --enroll-namespace --wait
```

This automatically labels the namespace with `istio.io/use-waypoint=waypoint` and routes all traffic through the waypoint for L7 inspection.

---

## Optional: Strict mTLS

To reject plaintext traffic from non-mesh sources:

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: finflow-strict-mtls
  namespace: finflow
spec:
  mtls:
    mode: STRICT
```

For a demo environment, the default `PERMISSIVE` mode (mTLS where available, plaintext otherwise) is fine.

---

## Local Development (No Kubernetes)

Three terminals:

```bash
# Terminal 1 — Orchestrator agent (port 8000)
cd agents/orchestrator && uv run python server.py

# Terminal 2 — BFF (port 8001)
cd bff && uv run uvicorn main:app --reload --port 8001

# Terminal 3 — UI dev server (port 3000)
cd ui && bun run dev
```

Open `http://localhost:3000`. The Next.js dev server proxies `/api/*` → `http://localhost:8001` automatically. No AgentGateway or AgentRegistry required for local development.

Run tests:

```bash
make test-all   # all MCP, agent, BFF, and UI tests
make test-bff   # BFF only
make test-ui    # UI only (uses bun)
```
