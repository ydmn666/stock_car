import type { StockOption, StockRecord } from "../types";

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

export type SetupMarket = "all" | "cn" | "us" | "hk";

export const HOT_STOCKS: StockOption[] = [
  { name: "比亚迪", code: "002594" },
  { name: "宁德时代", code: "300750" },
  { name: "长安汽车", code: "000625" },
  { name: "特斯拉", code: "TSLA" },
  { name: "蔚来", code: "NIO" },
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

export const FIELD_MAP = {
  close: ["收盘", "鏀剁洏", "close", "Close"],
  open: ["开盘", "寮€鐩?", "open", "Open"],
  high: ["最高", "鏈€楂?", "high", "High"],
  low: ["最低", "鏈€浣?", "low", "Low"],
  volume: ["成交量", "鎴愪氦閲?", "volume", "Volume"],
  pct: ["涨跌幅", "娑ㄨ穼骞?", "pct_change"],
  newsTime: ["发布时间", "鍙戝竷鏃堕棿", "date", "published_at"],
  newsTitle: ["新闻标题", "鏂伴椈鏍囬", "标题", "鏍囬", "title"],
};

export function today() {
  return new Date().toISOString().slice(0, 10);
}

export function oneYearAgo() {
  const date = new Date();
  date.setFullYear(date.getFullYear() - 1);
  return date.toISOString().slice(0, 10);
}

export function pick(record: StockRecord | undefined, keys: string[]) {
  if (!record) return null;
  for (const key of keys) {
    if (key in record) return record[key];
  }
  return null;
}

export function num(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function str(value: unknown) {
  return typeof value === "string" ? value : value == null ? "" : String(value);
}

export function money(value: number | null, prefix = "¥") {
  if (value == null) return "--";
  return `${prefix}${value.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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

export function scoreMetrics(records: StockRecord[]) {
  const closes = records.map((item) => num(pick(item, FIELD_MAP.close))).filter((value): value is number => value != null);
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

export function getNewsTitle(record: StockRecord) {
  return str(pick(record, FIELD_MAP.newsTitle) ?? "暂无标题");
}

export function getNewsTime(record: StockRecord) {
  return str(pick(record, FIELD_MAP.newsTime) ?? "--").slice(0, 19);
}

export function getNewsUrl(record: StockRecord) {
  for (const key of ["新闻链接", "鏂伴椈閾炬帴", "链接", "閾炬帴", "url", "URL", "source_url", "网址"]) {
    const value = record[key];
    if (typeof value === "string" && value.startsWith("http")) return value;
  }
  return "";
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
  activeStock: StockOption | null;
  selectedStocks: StockOption[];
  startDate: string;
  endDate: string;
  activeTab: WorkspaceTab;
  records: Record<string, StockRecord[]>;
  pdfCache: Record<string, PdfCacheItem>;
}) {
  const code = input.activeStock?.code ?? "";
  const pdfKey = code ? `${code}:${input.startDate}:${input.endDate}` : "";
  return {
    current_user: input.currentUser,
    current_stock_name: input.activeStock?.name ?? "",
    current_stock_code: code,
    selected_stocks: input.selectedStocks,
    active_tab: input.activeTab,
    analysis_ready: code ? (input.records[code] ?? []).length > 0 : false,
    start_date: input.startDate,
    end_date: input.endDate,
    pdf_ready_for_current_stock: pdfKey ? Boolean(input.pdfCache[pdfKey]) : false,
  };
}
