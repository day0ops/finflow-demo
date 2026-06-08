import uuid
from datetime import datetime, timezone


class OrderStore:
    """In-memory order store. Resets on restart (demo use only)."""

    def __init__(self):
        self._orders: dict[str, dict] = {}

    def create_order(
        self,
        user_id: str,
        ticker: str,
        action: str,
        shares: float,
        price: float,
    ) -> dict:
        order_id = str(uuid.uuid4())[:8].upper()
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "ticker": ticker.upper(),
            "action": action.upper(),  # BUY or SELL
            "shares": shares,
            "price": price,
            "total": round(shares * price, 2),
            "status": "FILLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> dict | None:
        return self._orders.get(order_id.upper())

    def list_orders(self, user_id: str) -> list[dict]:
        return [o for o in self._orders.values() if o["user_id"] == user_id]


ORDER_STORE = OrderStore()
