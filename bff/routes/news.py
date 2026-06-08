import mock as mock_data
from fastapi import APIRouter
from models import NewsResponse

router = APIRouter()


@router.get("/api/news", response_model=NewsResponse)
def get_news() -> NewsResponse:
    raw = mock_data.news()
    return NewsResponse(news=raw)
