import importlib
import importlib.util
import os
import sys

# Add brokerage-mcp to path so tests can import its FastMCP instance.
# We eagerly import the MCP server module here (while the path is correct)
# before pytest's collection phase can prepend the agent directory to sys.path.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
MCP_PATH = os.path.join(REPO_ROOT, "mcp-servers", "brokerage-mcp")
AGENT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

sys.path.insert(0, MCP_PATH)

# Force-import the MCP server module now under its canonical name, before pytest's
# importmode=prepend can re-prepend the agent dir (which has a conflicting server.py).
# After this, sys.modules["server"] == brokerage-mcp/server.py.
_mcp_server = importlib.import_module("server")  # resolves to brokerage-mcp/server.py

# Also pre-import the agent's server module under an alias so endpoint tests
# can import it without the name collision.
_agent_server_spec = importlib.util.spec_from_file_location(
    "agent_server",
    os.path.join(AGENT_PATH, "server.py"),
)
_agent_server_mod = importlib.util.module_from_spec(_agent_server_spec)
sys.modules["agent_server"] = _agent_server_mod
_agent_server_spec.loader.exec_module(_agent_server_mod)

import pytest  # noqa: E402
import store as brokerage_store  # noqa: E402
import tools as tools_module  # noqa: E402


@pytest.fixture(autouse=True)
def setup_brokerage(monkeypatch):
    brokerage_store.ORDER_STORE._orders.clear()
    monkeypatch.setattr(tools_module, "MCP_URL", _mcp_server.mcp)
    yield
    brokerage_store.ORDER_STORE._orders.clear()
