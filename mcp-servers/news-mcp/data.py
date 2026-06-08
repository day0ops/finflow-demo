import json
from pathlib import Path

_NEWS_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "news.json"


def load_news() -> dict:
    with open(_NEWS_FILE) as f:
        return json.load(f)


NEWS: dict = load_news()
