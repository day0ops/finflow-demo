import json
import sqlite3
from pathlib import Path

_SQL_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "holdings.sql"
_TICKERS_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "tickers.json"

with open(_TICKERS_FILE) as f:
    CURRENT_PRICES: dict = {k: v["price"] for k, v in json.load(f).items()}


def get_connection(db_path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
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
        positions.append(
            {
                "ticker": ticker,
                "shares": h["shares"],
                "cost_basis": h["cost_basis"],
                "current_price": price,
                "market_value": round(value, 2),
                "pl": round(pl, 2),
                "pl_pct": round(pl_pct, 2),
            }
        )

    return {
        "positions": positions,
        "total_cost": round(total_cost, 2),
        "total_value": round(total_value, 2),
        "total_pl": round(total_value - total_cost, 2),
        "total_pl_pct": round((total_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0.0,
    }
