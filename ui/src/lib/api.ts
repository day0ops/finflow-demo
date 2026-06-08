import type {
  User,
  TickerData,
  PortfolioData,
  PolicyState,
  PolicyKey,
  ChatRequest,
  ChatApiResponse,
  NewsData,
} from "./types";

const BASE = "/api";

export async function fetchTickers(): Promise<TickerData[]> {
  const res = await fetch(`${BASE}/tickers`);
  if (!res.ok) throw new Error(`Tickers fetch failed: ${res.status}`);
  const data = await res.json();
  return data.tickers as TickerData[];
}

export async function fetchPortfolio(): Promise<PortfolioData> {
  const res = await fetch(`${BASE}/portfolio`);
  if (!res.ok) throw new Error(`Portfolio fetch failed: ${res.status}`);
  return res.json() as Promise<PortfolioData>;
}

export async function fetchPolicies(): Promise<PolicyState> {
  const res = await fetch(`${BASE}/policies`);
  if (!res.ok) throw new Error(`Policies fetch failed: ${res.status}`);
  return res.json() as Promise<PolicyState>;
}

export async function togglePolicy(key: PolicyKey, value: boolean): Promise<PolicyState> {
  const res = await fetch(`${BASE}/policies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ [key]: value }),
  });
  if (!res.ok) throw new Error(`Policy update failed: ${res.status}`);
  return res.json() as Promise<PolicyState>;
}

export async function sendChat(req: ChatRequest): Promise<ChatApiResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Chat request failed: ${res.status}`);
  return res.json() as Promise<ChatApiResponse>;
}

export async function fetchMe(): Promise<User> {
  const res = await fetch(`${BASE}/me`);
  if (!res.ok) throw new Error(`Me fetch failed: ${res.status}`);
  return res.json() as Promise<User>;
}

export async function fetchNews(): Promise<NewsData> {
  const res = await fetch(`${BASE}/news`);
  if (!res.ok) throw new Error(`News fetch failed: ${res.status}`);
  return res.json() as Promise<NewsData>;
}
