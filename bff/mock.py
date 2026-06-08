import json
import sqlite3
from pathlib import Path

_MOCK_DIR = Path(__file__).parent.parent / "infra" / "mock-data"


def load_tickers() -> dict:
    with open(_MOCK_DIR / "tickers.json") as f:
        return json.load(f)


def get_holdings_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    sql = (_MOCK_DIR / "holdings.sql").read_text()
    conn.executescript(sql)
    conn.commit()
    return conn


_tickers: dict | None = None
_conn: sqlite3.Connection | None = None


def tickers() -> dict:
    global _tickers
    if _tickers is None:
        _tickers = load_tickers()
    return _tickers


def db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = get_holdings_conn()
    return _conn


_news: dict | None = None


def news() -> dict:
    global _news
    if _news is None:
        with open(_MOCK_DIR / "news.json") as f:
            _news = json.load(f)
    return _news
