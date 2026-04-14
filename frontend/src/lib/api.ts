import type {
  ForecastPoint,
  ForecastResponse,
  HistoryItem,
  Instrument,
  NewsResponse,
  PortfolioPerformanceResponse,
  PortfolioPosition,
  PortfolioSummary,
  PortfolioTransaction,
  PriceBar,
  PriceHistoryResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";
const AUTH_STORAGE_KEY = "stock-car-auth-session";

export type AuthSession = {
  token: string;
  username: string;
};

let authSession: AuthSession | null = readStoredSession();

function readStoredSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as Partial<AuthSession>;
    if (!parsed.token || !parsed.username) {
      return null;
    }
    return {
      token: parsed.token,
      username: parsed.username,
    };
  } catch {
    return null;
  }
}

export function getAuthSession() {
  return authSession;
}

export function setAuthSession(session: AuthSession) {
  authSession = session;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  }
}

export function clearAuthSession() {
  authSession = null;
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authSession?.token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${authSession.token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    if (response.status === 401) {
      clearAuthSession();
    }
    throw new Error(payload.detail ?? `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function getFilenameFromHeaders(response: Response, fallback: string) {
  const disposition = response.headers.get("Content-Disposition");
  if (!disposition) {
    return fallback;
  }
  const match = disposition.match(/filename="?([^"]+)"?/i);
  return match?.[1] ?? fallback;
}

export async function getHealth() {
  return request<{ status: string }>("/health");
}

export async function register(username: string, password: string) {
  return request<{ success: boolean; message: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function login(username: string, password: string) {
  return request<{ success: boolean; token?: string; username?: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function changePassword(oldPassword: string, newPassword: string) {
  return request<{ success: boolean; message: string }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword,
    }),
  });
}

export async function resolveInstrument(symbol: string, market?: Instrument["market"]) {
  return request<Instrument>("/instruments/resolve", {
    method: "POST",
    body: JSON.stringify({ symbol, market }),
  });
}

export async function getStockName(symbol: string, market?: Instrument["market"]) {
  const query = market ? `?market=${market}` : "";
  const payload = await request<{ name: string }>(`/stocks/name/${symbol}${query}`);
  return payload.name;
}

export async function getPriceHistory(instrument: Instrument, startDate: string, endDate: string) {
  return request<PriceHistoryResponse>("/stocks/data", {
    method: "POST",
    body: JSON.stringify({
      market: instrument.market,
      symbol: instrument.symbol,
      start_date: startDate,
      end_date: endDate,
    }),
  });
}

export async function getStockData(instrument: Instrument, startDate: string, endDate: string) {
  const payload = await getPriceHistory(instrument, startDate, endDate);
  return payload.records;
}

export async function getStockNews(instrument: Instrument, limit = 6) {
  return request<NewsResponse>("/stocks/news", {
    method: "POST",
    body: JSON.stringify({
      market: instrument.market,
      symbol: instrument.symbol,
      stock_name: instrument.display_name,
      limit,
    }),
  });
}

export async function getForecast(records: PriceBar[], days = 7) {
  return request<ForecastResponse>("/forecast", {
    method: "POST",
    body: JSON.stringify({ records, days }),
  });
}

export async function* streamAgent(messages: Array<{ role: string; content: string }>, context: Record<string, unknown>) {
  const response = await fetch(`${API_BASE_URL}/ai/agent/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(authSession?.token ? { Authorization: `Bearer ${authSession.token}` } : {}),
    },
    body: JSON.stringify({ messages, context }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    if (response.status === 401) {
      clearAuthSession();
    }
    throw new Error(payload.detail ?? `Request failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    return;
  }

  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    yield decoder.decode(value, { stream: true });
  }
}

export async function* streamAssistant(messages: Array<{ role: string; content: string }>, temperature = 1.1) {
  const response = await fetch(`${API_BASE_URL}/ai/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(authSession?.token ? { Authorization: `Bearer ${authSession.token}` } : {}),
    },
    body: JSON.stringify({ messages, temperature }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    if (response.status === 401) {
      clearAuthSession();
    }
    throw new Error(payload.detail ?? `Request failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    return;
  }

  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    yield decoder.decode(value, { stream: true });
  }
}

export async function generatePdfReport(instrument: Instrument, startDate: string, endDate: string) {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (authSession?.token) {
    headers.set("Authorization", `Bearer ${authSession.token}`);
  }

  const response = await fetch(`${API_BASE_URL}/reports/pdf`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      market: instrument.market,
      symbol: instrument.symbol,
      stock_name: instrument.display_name,
      start_date: startDate,
      end_date: endDate,
    }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    if (response.status === 401) {
      clearAuthSession();
    }
    throw new Error(payload.detail ?? `Request failed: ${response.status}`);
  }

  const filename = getFilenameFromHeaders(response, `${instrument.symbol}_report.pdf`);
  const bytes = await response.blob();
  return { filename, bytes };
}

export async function getUserHistory() {
  const payload = await request<{ items: HistoryItem[] }>("/users/me/history");
  return payload.items;
}

export async function logHistory(stockName: string, stockCode: string) {
  return request<{ success: boolean }>("/users/history/log", {
    method: "POST",
    body: JSON.stringify({
      stock_name: stockName,
      stock_code: stockCode,
    }),
  });
}

export async function deleteHistoryItem(itemId: number) {
  return request<{ success: boolean }>(`/users/history/${itemId}`, {
    method: "DELETE",
  });
}

export async function deleteAllUserHistory() {
  return request<{ success: boolean }>("/users/me/history", {
    method: "DELETE",
  });
}

export async function getPortfolioSummary() {
  return request<PortfolioSummary>("/portfolio/me/summary");
}

export async function getPortfolioPositions() {
  const payload = await request<{ items: PortfolioPosition[] }>("/portfolio/me/positions");
  return payload.items;
}

export async function getPortfolioPerformance() {
  return request<PortfolioPerformanceResponse>("/portfolio/me/performance");
}

export async function getPortfolioTransactions() {
  const payload = await request<{ items: PortfolioTransaction[] }>("/portfolio/me/transactions");
  return payload.items;
}

export async function createPortfolioTransaction(input: {
  symbol: string;
  trade_type: "buy" | "sell";
  trade_date: string;
  price: number;
  quantity: number;
  fee?: number;
  note?: string;
}) {
  return request<PortfolioTransaction>("/portfolio/transactions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updatePortfolioTransaction(
  transactionId: number,
  input: {
    symbol: string;
    trade_type: "buy" | "sell";
    trade_date: string;
    price: number;
    quantity: number;
    fee?: number;
    note?: string;
  },
) {
  return request<PortfolioTransaction>(`/portfolio/transactions/${transactionId}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export async function deletePortfolioTransaction(transactionId: number) {
  return request<{ success: boolean }>(`/portfolio/transactions/${transactionId}`, {
    method: "DELETE",
  });
}

export type { ForecastPoint, PriceBar };
