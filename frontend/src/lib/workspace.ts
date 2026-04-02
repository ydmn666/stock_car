import type { Instrument, NewsItem, PriceBar } from "../types";

export type WorkspaceTab =
  | "overview"
  | "market"
  | "technical"
  | "sentiment"
  | "forecast"
  | "portfolio"
  | "history";

export type AgentMessage = { role: "user" | "assistant"; content: string };

export type PdfCacheItem = { filename: string; blob: Blob };

export type SetupMarket = "cn";

export const HOT_STOCKS: Instrument[] = [
  { id: "CN:002594", market: "CN", symbol: "002594", full_symbol: "002594.SZ", asset_type: "stock", display_name: "比亚迪", exchange: "SZSE", currency: "CNY" },
  { id: "CN:300750", market: "CN", symbol: "300750", full_symbol: "300750.SZ", asset_type: "stock", display_name: "宁德时代", exchange: "SZSE", currency: "CNY" },
  { id: "CN:000625", market: "CN", symbol: "000625", full_symbol: "000625.SZ", asset_type: "stock", display_name: "长安汽车", exchange: "SZSE", currency: "CNY" },
];

export const WORKSPACE_TABS: Array<{ key: WorkspaceTab; label: string; short: string }> = [
  { key: "overview", label: "总览", short: "总" },
  { key: "market", label: "市场分析", short: "市" },
  { key: "technical", label: "技术分析", short: "技" },
  { key: "sentiment", label: "资讯舆情", short: "讯" },
  { key: "forecast", label: "趋势预测", short: "势" },
  { key: "portfolio", label: "个人投资", short: "投" },
  { key: "history", label: "历史记录", short: "史" },
];

export function today() {
  return new Date().toISOString().slice(0, 10);
}

export function oneYearAgo() {
  const date = new Date();
  date.setFullYear(date.getFullYear() - 1);
  return date.toISOString().slice(0, 10);
}

export function num(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function money(value: number | null, prefix = "￥") {
  if (value == null) return "--";
  return `${prefix}${value.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function pricePrefix(instrument: Instrument | null | undefined) {
  return "￥";
}

export function percent(value: number | null, digits = 2) {
  if (value == null) return "--";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

export function markdown(value: string) {
  return value.replace(/^```markdown\s*/i, "").replace(/^```/i, "").replace(/```$/i, "").trim();
}

export function pdfIntent(text: string) {
  const lower = text.toLowerCase();
  return lower.includes("pdf") || text.includes("报告") || text.includes("导出") || text.includes("下载");
}

export function scoreMetrics(records: PriceBar[]) {
  const closes = records.map((item) => item.close).filter((value): value is number => value != null);
  if (closes.length < 5) return { total: null, drawdown: null, volatility: null };
  const returns: number[] = [];
  for (let index = 1; index < closes.length; index += 1) {
    const prev = closes[index - 1];
    const current = closes[index];
    if (prev) returns.push((current - prev) / prev);
  }
  const average = returns.reduce((sum, item) => sum + item, 0) / Math.max(returns.length, 1);
  const variance = returns.reduce((sum, item) => sum + (item - average) ** 2, 0) / Math.max(returns.length - 1, 1);
  const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100;
  let peak = closes[0];
  let drawdown = 0;
  for (const close of closes) {
    peak = Math.max(peak, close);
    drawdown = Math.min(drawdown, close / peak - 1);
  }
  const total = closes[0] ? ((closes[closes.length - 1] - closes[0]) / closes[0]) * 100 : 0;
  return { total, drawdown: drawdown * 100, volatility };
}

export function getNewsTitle(record: NewsItem) {
  return record.title || "暂无标题";
}

export function getNewsTime(record: NewsItem) {
  return record.published_at.slice(0, 19) || "--";
}

export function getNewsUrl(record: NewsItem) {
  return record.url || "";
}

export function download(item: PdfCacheItem) {
  const url = URL.createObjectURL(item.blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = item.filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 300);
}

export function buildContext(input: {
  currentUser: string;
  activeStock: Instrument | null;
  selectedStocks: Instrument[];
  startDate: string;
  endDate: string;
  activeTab: WorkspaceTab;
  records: Record<string, PriceBar[]>;
  pdfCache: Record<string, PdfCacheItem>;
}) {
  const instrumentId = input.activeStock?.id ?? "";
  const pdfKey = instrumentId ? `${instrumentId}:${input.startDate}:${input.endDate}` : "";
  return {
    current_user: input.currentUser,
    current_stock_name: input.activeStock?.display_name ?? "",
    current_stock_code: input.activeStock?.symbol ?? "",
    current_market: input.activeStock?.market ?? "",
    selected_stocks: input.selectedStocks.map((item) => ({
      market: item.market,
      symbol: item.symbol,
      full_symbol: item.full_symbol,
      display_name: item.display_name,
    })),
    active_tab: input.activeTab,
    analysis_ready: instrumentId ? (input.records[instrumentId] ?? []).length > 0 : false,
    start_date: input.startDate,
    end_date: input.endDate,
    pdf_ready_for_current_stock: pdfKey ? Boolean(input.pdfCache[pdfKey]) : false,
  };
}

