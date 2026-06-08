import mock as mock_data
from auth import get_user
from fastapi import APIRouter, Request
from models import HoldingOut, PortfolioResponse

router = APIRouter()


@router.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio(request: Request) -> PortfolioResponse:
    user_id = get_user(request).username
    price_map = mock_data.tickers()
    rows = (
        mock_data.db()
        .execute(
            "SELECT ticker, shares, cost_basis FROM holdings WHERE user_id=?",
            (user_id,),
        )
        .fetchall()
    )
    holdings: list[HoldingOut] = []
    total = 0.0
    total_cost = 0.0
    for ticker, shares, cost_basis in rows:
        if ticker not in price_map:
            continue
        current = price_map[ticker]["price"]
        market_value = round(shares * current, 2)
        pnl_pct = round((current - cost_basis) / cost_basis * 100, 2)
        pnl = round(market_value - shares * cost_basis, 2)
        total += market_value
        total_cost += shares * cost_basis
        holdings.append(
            HoldingOut(
                ticker=ticker,
                name=price_map[ticker]["name"],
                shares=shares,
                cost_basis=cost_basis,
                current_price=current,
                market_value=market_value,
                pnl_pct=pnl_pct,
                pnl=pnl,
            )
        )
    total_pl = round(total - total_cost, 2)
    total_pl_pct = round((total - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0.0
    return PortfolioResponse(
        holdings=holdings, total_value=round(total, 2), total_pl=total_pl, total_pl_pct=total_pl_pct
    )
