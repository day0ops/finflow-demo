export interface User {
  username: string;
  display_name: string;
  role: string;
}

export interface TickerData {
  ticker: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number;
  history: Array<{ date: string; close: number }>;
}

export interface Holding {
  ticker: string;
  name: string;
  shares: number;
  cost_basis: number;
  current_price: number;
  market_value: number;
  pnl_pct: number;
  pnl: number;
}

export interface PortfolioData {
  holdings: Holding[];
  total_value: number;
  total_pl: number;
  total_pl_pct: number;
}

export interface PolicyState {
  rbac: boolean;
  elicitation: boolean;
  rate_limit: boolean;
  guardrails: boolean;
}

export type PolicyKey = keyof PolicyState;

export interface PolicyEvent {
  type: string;
  policy: string;
  verdict: "allow" | "deny";
  message: string;
}

export interface TraceData {
  intent: "briefing" | "trade" | "unknown";
  agents: string[];
  latency_ms: number;
  status_code: number;
  policy_events: PolicyEvent[];
}

export interface ElicitationData {
  required: true;
  prompt: string;
  trade_details: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent_tag?: "BRIEFING" | "TRADE" | "ELICITATION";
  agent_name?: string;
  latency_ms?: number;
  policy_events?: PolicyEvent[];
  blocked?: boolean;
  elicitation?: ElicitationData;
}

export interface ChatRequest {
  message: string;
  session_id: string;
  confirmed?: boolean;
}

export interface ChatApiResponse {
  message: string;
  trace: TraceData;
  elicitation?: ElicitationData;
}

export interface NewsItem {
  headline: string;
  source: string;
  date: string;
  sentiment: "positive" | "negative" | "neutral";
  score: number;
}

export interface NewsData {
  news: Record<string, NewsItem[]>;
}
