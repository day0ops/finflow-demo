import json

from data import TICKERS
from fastmcp import FastMCP

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
    return json.dumps(
        {
            "ticker": data["ticker"],
            "name": data["name"],
            "price": data["price"],
            "change_pct": data["change_pct"],
            "volume": data["volume"],
            "sector": data["sector"],
        }
    )


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
