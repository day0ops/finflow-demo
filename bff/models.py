from pydantic import BaseModel


class TickerOut(BaseModel):
    ticker: str
    name: str
    price: float
    change_pct: float
    volume: int
    history: list[dict] = []


class TickersResponse(BaseModel):
    tickers: list[TickerOut]


class HoldingOut(BaseModel):
    ticker: str
    name: str
    shares: float
    cost_basis: float
    current_price: float
    market_value: float
    pnl_pct: float
    pnl: float


class PortfolioResponse(BaseModel):
    holdings: list[HoldingOut]
    total_value: float
    total_pl: float
    total_pl_pct: float


class PolicyState(BaseModel):
    rbac: bool = False
    elicitation: bool = False
    rate_limit: bool = False
    guardrails: bool = False


class PolicyUpdate(BaseModel):
    rbac: bool | None = None
    elicitation: bool | None = None
    rate_limit: bool | None = None
    guardrails: bool | None = None


class PolicyEvent(BaseModel):
    type: str
    policy: str
    verdict: str
    message: str


class TraceData(BaseModel):
    intent: str
    agents: list[str]
    latency_ms: int
    status_code: int
    policy_events: list[PolicyEvent]


class ElicitationData(BaseModel):
    required: bool = True
    prompt: str
    trade_details: str


class ChatRequest(BaseModel):
    message: str
    session_id: str
    confirmed: bool = False


class ChatResponse(BaseModel):
    message: str
    trace: TraceData
    elicitation: ElicitationData | None = None


class NewsItem(BaseModel):
    headline: str
    source: str
    date: str
    sentiment: str  # "positive" | "negative" | "neutral"
    score: float


class NewsResponse(BaseModel):
    news: dict[str, list[NewsItem]]  # ticker -> list of items
