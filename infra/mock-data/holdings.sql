CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    shares REAL NOT NULL,
    cost_basis REAL NOT NULL,
    UNIQUE(user_id, ticker)
);

INSERT OR REPLACE INTO holdings (user_id, ticker, shares, cost_basis) VALUES
  ('morgan', 'NVDA',  100.0,  95.40),
  ('morgan', 'AAPL',   50.0, 155.20),
  ('morgan', 'MSFT',  200.0, 380.90),
  ('morgan', 'GOOGL',  30.0, 148.60),
  ('alex',   'AAPL',   50.0, 160.50),
  ('alex',   'MSFT',  100.0, 395.20);
