import type { ForecastResponse, HistoryItem, NewsResponse, StockRecord } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
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
  return request<{ success: boolean }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function getStockName(symbol: string) {
  const payload = await request<{ name: string }>(`/stocks/name/${symbol}`);
  return payload.name;
}

export async function getStockData(symbol: string, startDate: string, endDate: string) {
  const payload = await request<{ records: StockRecord[] }>("/stocks/data", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      start_date: startDate,
      end_date: endDate,
    }),
  });
  return payload.records;
}

export async function getStockNews(symbol: string, stockName?: string, limit = 6) {
  return request<NewsResponse>("/stocks/news", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      stock_name: stockName,
      limit,
    }),
  });
}

export async function getForecast(records: StockRecord[], days = 7) {
  return request<ForecastResponse>("/forecast", {
    method: "POST",
    body: JSON.stringify({
      records,
      days,
    }),
  });
}

export async function* streamAgent(messages: Array<{ role: string; content: string }>, context: Record<string, unknown>) {
  const response = await fetch(`${API_BASE_URL}/ai/agent/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ messages, context }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
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
    },
    body: JSON.stringify({ messages, temperature }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
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

export async function generatePdfReport(symbol: string, stockName: string, startDate: string, endDate: string) {
  const response = await fetch(`${API_BASE_URL}/reports/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      symbol,
      stock_name: stockName,
      start_date: startDate,
      end_date: endDate,
    }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? `Request failed: ${response.status}`);
  }

  const filename = getFilenameFromHeaders(response, `${symbol}_report.pdf`);
  const bytes = await response.blob();
  return { filename, bytes };
}

export async function getUserHistory(username: string) {
  const payload = await request<{ items: HistoryItem[] }>(`/users/${username}/history`);
  return payload.items;
}

export async function logHistory(username: string, stockName: string, stockCode: string) {
  return request<{ success: boolean }>("/users/history/log", {
    method: "POST",
    body: JSON.stringify({
      username,
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

export async function deleteAllUserHistory(username: string) {
  return request<{ success: boolean }>(`/users/${username}/history`, {
    method: "DELETE",
  });
}
