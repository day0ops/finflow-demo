import json
import os
import sqlite3

from db import CURRENT_PRICES, calculate_pl, get_connection, get_holdings, seed_db
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP("portfolio-mcp")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


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
        return json.dumps(
            {
                "user_id": user_id,
                "positions": [],
                "total_cost": 0,
                "total_value": 0,
                "total_pl": 0,
                "total_pl_pct": 0,
            }
        )
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
        allocation.append(
            {
                "ticker": h["ticker"],
                "market_value": round(value, 2),
                "pct_of_portfolio": round(value / total_value * 100, 2),
            }
        )
    allocation.sort(key=lambda x: x["pct_of_portfolio"], reverse=True)

    return json.dumps({"user_id": user_id, "total_value": round(total_value, 2), "allocation": allocation})


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
