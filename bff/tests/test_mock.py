def test_load_tickers_has_expected_symbols():
    from mock import load_tickers

    data = load_tickers()
    assert "NVDA" in data
    assert "AAPL" in data
    assert "MSFT" in data
    assert data["NVDA"]["price"] > 0
    assert isinstance(data["NVDA"]["change_pct"], float)


def test_load_holdings_morgan_has_four_rows():
    from mock import get_holdings_conn

    conn = get_holdings_conn()
    rows = conn.execute("SELECT ticker FROM holdings WHERE user_id='morgan'").fetchall()
    assert len(rows) == 4
    tickers = {r[0] for r in rows}
    assert "NVDA" in tickers
    assert "AAPL" in tickers


def test_singleton_tickers_returns_same_object():
    from mock import tickers

    a = tickers()
    b = tickers()
    assert a is b


def test_singleton_db_returns_same_connection():
    from mock import db

    a = db()
    b = db()
    assert a is b
