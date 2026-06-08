import json
from pathlib import Path

_DATA_FILE = Path(__file__).parent.parent.parent / "infra" / "mock-data" / "tickers.json"


def load_tickers() -> dict:
    with open(_DATA_FILE) as f:
        return json.load(f)


TICKERS: dict = load_tickers()
