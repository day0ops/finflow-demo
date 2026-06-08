from enum import Enum


class Intent(str, Enum):
    BRIEFING = "briefing"
    TRADE = "trade"
    UNKNOWN = "unknown"


_TRADE_KEYWORDS = {"trade", "buy", "sell", "execute", "purchase", "shares"}
_BRIEFING_KEYWORDS = {
    "portfolio",
    "briefing",
    "holdings",
    "performance",
    "overview",
    "picture",
    "context",
    "news",
}


def detect_intent(text: str) -> Intent:
    words = set(text.lower().split())
    if words & _TRADE_KEYWORDS:
        return Intent.TRADE
    if words & _BRIEFING_KEYWORDS:
        return Intent.BRIEFING
    return Intent.UNKNOWN
