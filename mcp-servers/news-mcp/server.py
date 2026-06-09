import json

from data import NEWS
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP("news-mcp")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


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
    return json.dumps(
        {
            "ticker": ticker.upper(),
            "articles": articles[:limit],
        }
    )


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
            results.append(
                {
                    "ticker": ticker.upper(),
                    "avg_score": 0.0,
                    "sentiment": "neutral",
                    "article_count": 0,
                }
            )
            continue
        avg_score = round(sum(a["score"] for a in articles) / len(articles), 2)
        if avg_score > 0.3:
            sentiment = "positive"
        elif avg_score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        results.append(
            {
                "ticker": ticker.upper(),
                "avg_score": avg_score,
                "sentiment": sentiment,
                "article_count": len(articles),
                "top_headline": articles[0]["headline"],
            }
        )

    all_scores = [r["avg_score"] for r in results]
    overall_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    return json.dumps(
        {
            "tickers": results,
            "overall_score": overall_score,
            "overall_sentiment": "positive"
            if overall_score > 0.3
            else "negative"
            if overall_score < -0.2
            else "neutral",
        }
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
