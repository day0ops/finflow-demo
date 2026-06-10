import os

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams


def _connect_timeout() -> float:
    try:
        return float(os.environ.get("MCP_CONNECT_TIMEOUT", "60"))
    except ValueError:
        return 60.0


def get_mcp_tools() -> list:
    url = os.getenv("PORTFOLIO_MCP_URL", "http://agentgateway.finflow.svc/mcp/portfolio/mcp/")
    return [MCPToolset(connection_params=StreamableHTTPConnectionParams(url=url, timeout=_connect_timeout()))]
