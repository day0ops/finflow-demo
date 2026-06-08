import mock as mock_data
from fastapi import APIRouter
from models import TickerOut, TickersResponse

router = APIRouter()


@router.get("/api/tickers", response_model=TickersResponse)
def get_tickers() -> TickersResponse:
    data = mock_data.tickers()
    return TickersResponse(
        tickers=[
            TickerOut(
                ticker=v["ticker"],
                name=v["name"],
                price=v["price"],
                change_pct=v["change_pct"],
                volume=v["volume"],
                history=v.get("history", []),
            )
            for v in data.values()
        ]
    )
