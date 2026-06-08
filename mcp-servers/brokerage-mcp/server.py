import json
from pathlib import Path

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
