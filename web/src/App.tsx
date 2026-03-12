import { FormEvent, Suspense, lazy, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  generatePdfReport,
  getForecast,
  getHealth,
  getStockData,
  getStockName,
  getStockNews,
  getUserHistory,
  logHistory,
  login,
  register,
  deleteHistoryItem,
  deleteAllUserHistory,
  streamAgent,
  streamAssistant,
} from "./lib/api";
import type { HistoryItem, StockOption, StockRecord } from "./types";

const KLineChart = lazy(() => import("./components/charts").then((module) => ({ default: module.KLineChart })));
const ReturnChart = lazy(() => import("./components/charts").then((module) => ({ default: module.ReturnChart })));
const ComparisonChart = lazy(() => import("./components/charts").then((module) => ({ default: module.ComparisonChart })));
const ForecastChart = lazy(() => import("./components/charts").then((module) => ({ default: module.ForecastChart })));
const SentimentGaugeChart = lazy(() => import("./components/charts").then((module) => ({ default: module.SentimentGaugeChart })));

const HOT_STOCKS: StockOption[] = [
  { name: "比亚迪", code: "002594" },
  { name: "宁德时代", code: "300750" },
  { name: "赛力斯", code: "601127" },
  { name: "长安汽车", code: "000625" },
  { name: "长城汽车", code: "601633" },
];

type AgentMessage = {
  role: "user" | "assistant";
  content: string;
};

type PdfCacheItem = {
  filename: string;
  blob: Blob;
};

type ActiveTab = "data" | "technical" | "forecast" | "news";

function today() {
  return new Date().toISOString().slice(0, 10);
}

function oneYearAgo() {
  const value = new Date();
  value.setFullYear(value.getFullYear() - 1);
  return value.toISOString().slice(0, 10);
}

function getNumber(record: StockRecord | undefined, key: string) {
  const value = record?.[key];
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function formatMetric(value: number | null, digits = 2, suffix = "") {
  if (value == null || Number.isNaN(value)) {
    return "--";
  }
  return `${value.toFixed(digits)}${suffix}`;
}

function downloadPdf(item: PdfCacheItem) {
  const url = URL.createObjectURL(item.blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = item.filename;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  window.setTimeout(() => {
    URL.revokeObjectURL(url);
    link.remove();
  }, 300);
}

function isPdfIntent(text: string) {
  const value = text.toLowerCase();
  return (
    value.includes("pdf") ||
    value.includes("report") ||
    text.includes("报告") ||
    text.includes("下载") ||
    text.includes("导出")
  );
}

function buildAgentContext(input: {
  activeCode: string;
  selectedStocks: StockOption[];
  startDate: string;
  endDate: string;
  records: Record<string, StockRecord[]>;
  pdfCache: Record<string, PdfCacheItem>;
}) {
  const activeStock = input.selectedStocks.find((item) => item.code === input.activeCode);
  const analysisReady = activeStock ? (input.records[activeStock.code] ?? []).length > 0 : false;
  const cacheKey = activeStock ? `${activeStock.code}:${input.startDate}:${input.endDate}` : "";

  return {
    analysis_ready: analysisReady,
    current_stock_name: activeStock?.name ?? "",
    current_stock_code: activeStock?.code ?? "",
    start_date: input.startDate,
    end_date: input.endDate,
    pdf_ready_for_current_stock: cacheKey ? Boolean(input.pdfCache[cacheKey]) : false,
  };
}

function calculateMetrics(records: StockRecord[]) {
  const closes = records.map((record) => getNumber(record, "收盘")).filter((value): value is number => value != null);
  if (closes.length < 5) {
    return { volatility: null, sharpe: null, maxDrawdown: null };
  }

  const returns: number[] = [];
  for (let index = 1; index < closes.length; index += 1) {
    const prev = closes[index - 1];
    const curr = closes[index];
    if (prev !== 0) {
      returns.push((curr - prev) / prev);
    }
  }

  const mean = returns.reduce((sum, value) => sum + value, 0) / Math.max(returns.length, 1);
  const variance = returns.reduce((sum, value) => sum + (value - mean) ** 2, 0) / Math.max(returns.length - 1, 1);
  const volatility = Math.sqrt(variance) * Math.sqrt(252);
  const sharpe = volatility === 0 ? 0 : (mean * 252 - 0.02) / volatility;

  let peak = closes[0];
  let maxDrawdown = 0;
  for (const close of closes) {
    peak = Math.max(peak, close);
    maxDrawdown = Math.min(maxDrawdown, close / peak - 1);
  }

  return { volatility, sharpe, maxDrawdown };
}

function buildTechnicalPrompt(stockName: string, records: StockRecord[], comparisonSeries: Array<{ name: string; records: StockRecord[] }>) {
  if (records.length < 2) {
    return null;
  }

  const last = records[records.length - 1];
  const prev = records[records.length - 2];
  const closes = records.map((record) => getNumber(record, "收盘")).filter((value): value is number => value != null);
  const average = (days: number) => {
    const slice = closes.slice(Math.max(0, closes.length - days));
    return slice.reduce((sum, value) => sum + value, 0) / Math.max(slice.length, 1);
  };

  const startClose = closes[0];
  const endClose = closes[closes.length - 1];
  const totalReturn = startClose === 0 ? 0 : ((endClose - startClose) / startClose) * 100;
  const volumeRatio = (getNumber(last, "成交量") ?? 0) / Math.max(getNumber(prev, "成交量") ?? 1, 1);
  const comparisonText = comparisonSeries
    .filter((item) => item.name !== stockName && item.records.length > 1)
    .map((item) => {
      const start = getNumber(item.records[0], "收盘");
      const end = getNumber(item.records[item.records.length - 1], "收盘");
      const pct = start ? (((end ?? start) - start) / start) * 100 : 0;
      return `- ${item.name}: 区间收益率 ${pct.toFixed(2)}%`;
    })
    .join("\n");

  return `
你是一位资深金融分析师，尤其擅长中国新能源车产业链研究。请根据用户给出的客观交易数据，结合行业背景知识，输出一份专业、克制的分析报告。

分析对象：${stockName}
- 最新收盘价: ${formatMetric(getNumber(last, "收盘"))}
- 当日涨跌幅: ${formatMetric(getNumber(last, "涨跌幅"), 2, "%")}
- 换手率: ${formatMetric(getNumber(last, "换手率"), 2, "%")}
- 量比近似: ${volumeRatio.toFixed(2)}
- MA5: ${average(5).toFixed(2)}
- MA10: ${average(10).toFixed(2)}
- MA20: ${average(20).toFixed(2)}
- 区间累计收益率: ${totalReturn.toFixed(2)}%

行业对比：
${comparisonText || "暂无其他对比数据"}

要求：
1. 不要机械解释指标，要结合行业逻辑。
2. 明确机会、风险和当前交易位置。
3. 输出 Markdown。
`.trim();
}

function buildForecastPrompt(stockName: string, forecast: StockRecord[]) {
  if (!forecast.length) {
    return null;
  }

  const future = forecast.slice(-7);
  const start = getNumber(future[0], "yhat");
  const end = getNumber(future[future.length - 1], "yhat");
  const upper = getNumber(future[future.length - 1], "yhat_upper");
  const lower = getNumber(future[future.length - 1], "yhat_lower");
  if (start == null || end == null || upper == null || lower == null) {
    return null;
  }

  const growth = start === 0 ? 0 : ((end - start) / start) * 100;
  const uncertainty = end === 0 ? 0 : ((upper - lower) / end) * 100;

  return `
你是一位量化策略顾问。下面是一份由 Prophet 生成的 7 天股价预测结果。

分析对象：${stockName}
- 模型方向: ${growth >= 0 ? "看涨" : "看跌"}
- 理论涨跌幅: ${growth.toFixed(2)}%
- 理论目标价: ${end.toFixed(2)}
- 不确定性区间: ${uncertainty.toFixed(2)}%

请完成两件事：
1. 先直接说明模型判断未来一周是涨还是跌。
2. 再结合行业和基本面角度，评价这个预测是否可信。
3. 输出 Markdown。
`.trim();
}

function buildPriceTrendSummary(records: StockRecord[]) {
  if (!records.length) {
    return "暂无行情数据。";
  }
  const firstClose = getNumber(records[0], "收盘");
  const lastClose = getNumber(records[records.length - 1], "收盘");
  const highs = records.map((item) => getNumber(item, "最高")).filter((value): value is number => value != null);
  const lows = records.map((item) => getNumber(item, "最低")).filter((value): value is number => value != null);
  if (firstClose == null || lastClose == null || !highs.length || !lows.length) {
    return "暂无行情数据。";
  }

  const change = ((lastClose - firstClose) / firstClose) * 100;
  const high = Math.max(...highs);
  const low = Math.min(...lows);
  const fromHigh = ((lastClose - high) / high) * 100;
  const fromLow = ((lastClose - low) / low) * 100;
  return `最新收盘价 ${lastClose.toFixed(2)} 元，区间涨跌幅 ${change.toFixed(2)}%，相对区间高点回撤 ${fromHigh.toFixed(2)}%，相对区间低点反弹 ${fromLow.toFixed(2)}%。`;
}

function buildSentimentPrompt(stockName: string, news: StockRecord[], records: StockRecord[], metrics: ReturnType<typeof calculateMetrics>, isFallback: boolean) {
  if (!news.length) {
    return null;
  }
  const newsText = news
    .slice(0, 10)
    .map((item) => `- [${String(item["发布时间"] ?? "近期").slice(0, 10)}] ${String(item["新闻标题"] ?? item["标题"] ?? item["内容"] ?? "")}`)
    .join("\n");
  const metricsText =
    metrics.volatility == null
      ? "暂无量化指标"
      : `- 年化波动率: ${(metrics.volatility * 100).toFixed(2)}%\n- 夏普比率: ${metrics.sharpe?.toFixed(2)}\n- 最大回撤: ${((metrics.maxDrawdown ?? 0) * 100).toFixed(2)}%`;

  return `
你是一位交易员。请基于最新市场信息，对 ${stockName} 做舆情与情绪分析。
资讯来源：${isFallback ? "行业新闻回退" : "个股新闻"}

量化指标：
${metricsText}

行情摘要：
${buildPriceTrendSummary(records)}

最新资讯：
${newsText}

输出格式必须严格如下：
SCORE: [0-100]
ANALYSIS: [分析内容]
`.trim();
}

function parseSentiment(content: string) {
  const scoreMatch = content.match(/SCORE:\s*(\d+)/i);
  const analysisMatch = content.match(/ANALYSIS:\s*([\s\S]*)/i);
  return {
    score: scoreMatch ? Math.max(0, Math.min(100, Number(scoreMatch[1]))) : null,
    analysis: analysisMatch ? analysisMatch[1].trim() : content.trim(),
  };
}

function getNewsLink(record: StockRecord) {
  const candidateKeys = ["新闻链接", "链接", "url", "URL", "网址", "source_url"];
  for (const key of candidateKeys) {
    const value = record[key];
    if (typeof value === "string" && value.startsWith("http")) {
      return value;
    }
  }
  for (const value of Object.values(record)) {
    if (typeof value === "string" && value.startsWith("http")) {
      return value;
    }
  }
  return "";
}

function SectionHeader(props: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">{props.eyebrow}</p>
        <h3 className="mt-2 text-3xl font-semibold text-slate-950">{props.title}</h3>
      </div>
      <p className="max-w-2xl text-sm leading-7 text-slate-500">{props.description}</p>
    </div>
  );
}

function MetricCard(props: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-white px-5 py-4 shadow-sm">
      <p className="text-sm text-slate-500">{props.label}</p>
      <p className="mt-3 text-3xl font-semibold text-slate-900">{props.value}</p>
    </div>
  );
}

function EmptyState(props: { text: string }) {
  return <div className="rounded-[28px] border border-dashed border-slate-300 bg-white px-6 py-12 text-center text-slate-500">{props.text}</div>;
}

function ChartLoading() {
  return <div className="rounded-[28px] border border-slate-200 bg-white px-6 py-16 text-center text-slate-500">图表加载中...</div>;
}

function sanitizeMarkdown(content: string) {
  return content
    .replace(/^["'`]+/g, "")
    .replace(/^markdown\s*/i, "")
    .replace(/^```markdown\s*/i, "")
    .replace(/^```md\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/\s*```$/i, "")
    .replace(/```/g, "")
    .replace(/-{3,}/g, "")
    .replace(/^\s*[-_]{3,}\s*$/gm, "")
    .replace(/(?<!\n)(#{1,3}\s)/g, "\n$1")
    .replace(/(?<!\n)([-*]\s)/g, "\n$1")
    .replace(/(?<!\n)(\d+\.\s)/g, "\n$1")
    .replace(/\s+\|\s+/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function MarkdownPanel(props: { content: string; emptyText: string; className?: string }) {
  const text = sanitizeMarkdown(props.content);
  if (!text) {
    return <div className={props.className}>{props.emptyText}</div>;
  }

  return (
    <div className={props.className}>
      <div className="prose prose-slate max-w-none prose-headings:mb-3 prose-headings:mt-6 prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-p:leading-8 prose-li:leading-8 prose-strong:text-slate-900 prose-table:block prose-table:overflow-x-auto prose-th:text-left prose-td:align-top">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
      </div>
    </div>
  );
}

function RecordTable(props: { records: StockRecord[]; limit?: number }) {
  const rows = [...props.records]
    .sort((left, right) => {
      const leftDate = String(left["日期"] ?? left["date"] ?? "");
      const rightDate = String(right["日期"] ?? right["date"] ?? "");
      return rightDate.localeCompare(leftDate);
    })
    .slice(0, props.limit ?? props.records.length);
  return (
    <div className="max-h-[720px] overflow-auto rounded-[24px] border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="sticky top-0 bg-slate-50">
          <tr>
            {Object.keys(rows[0] ?? {}).slice(0, 12).map((key) => (
              <th key={key} className="px-4 py-3 text-left font-medium text-slate-500">
                {key}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((record, index) => (
            <tr key={index}>
              {Object.entries(record)
                .slice(0, 12)
                .map(([key, value]) => (
                  <td key={key} className="px-4 py-3 text-slate-700">
                    {String(value ?? "")}
                  </td>
                ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AgentPanel(props: {
  currentUser: string;
  selectedStocks: StockOption[];
  activeCode: string;
  startDate: string;
  endDate: string;
  records: Record<string, StockRecord[]>;
  pdfCache: Record<string, PdfCacheItem>;
  onRequestPdf: () => Promise<boolean | void>;
}) {
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      role: "assistant",
      content: "你好，我是通用股票助理。你可以直接问股票代码、公司基础资料、行业概念，也可以让我处理当前股票的 PDF。",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = input.trim();
    if (!prompt) {
      return;
    }

    const nextMessages: AgentMessage[] = [...messages, { role: "user", content: prompt }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    try {
      if (isPdfIntent(prompt)) {
        const ok = await props.onRequestPdf();
        setMessages((current) => [
          ...current,
          {
            role: "assistant",
            content: ok
              ? "当前股票的 PDF 报告已经开始下载。"
              : "当前还不能生成或下载 PDF。请先点击左侧“生成分析报告”，确保当前股票分析结果已经加载完成。",
          },
        ]);
        return;
      }

      const assistantIndex = nextMessages.length;
      setMessages((current) => [...current, { role: "assistant", content: "" }]);
      let content = "";
      for await (const chunk of streamAgent(
        nextMessages.map((message) => ({ role: message.role, content: message.content })),
        buildAgentContext({
          activeCode: props.activeCode,
          selectedStocks: props.selectedStocks,
          startDate: props.startDate,
          endDate: props.endDate,
          records: props.records,
          pdfCache: props.pdfCache,
        }),
      )) {
        content += chunk;
        setMessages((current) =>
          current.map((message, index) => (index === assistantIndex ? { ...message, content } : message)),
        );
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        { role: "assistant", content: error instanceof Error ? error.message : "通用 Agent 调用失败。" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Agent</p>
          <h3 className="mt-2 text-2xl font-semibold text-slate-950">通用聊天</h3>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">{props.currentUser}</span>
      </div>
      <p className="text-sm leading-7 text-slate-500">右侧始终显示通用 Agent。它不属于四个分功能页，直接调用你现有的通用聊天链路。</p>

      <div className="mt-5 h-[620px] space-y-3 overflow-y-auto rounded-[28px] bg-slate-50 p-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`rounded-2xl px-4 py-3 text-sm leading-7 ${
              message.role === "user"
                ? "ml-auto max-w-[88%] bg-slate-950 text-white"
                : "max-w-[92%] bg-white text-slate-700 ring-1 ring-slate-200"
            }`}
          >
            {message.role === "user" ? (
              message.content
            ) : (
              <MarkdownPanel content={message.content} emptyText="" className="text-sm leading-7 text-slate-700" />
            )}
          </div>
        ))}
        {loading ? <div className="max-w-[92%] rounded-2xl bg-white px-4 py-3 text-sm text-slate-500 ring-1 ring-slate-200">Agent 正在处理...</div> : null}
      </div>

      <form className="mt-4 flex gap-3" onSubmit={handleSubmit}>
        <input
          className="min-w-0 flex-1 rounded-2xl border border-slate-200 px-4 py-3 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100"
          placeholder="直接输入股票代码、概念、公司问题..."
          value={input}
          onChange={(event) => setInput(event.target.value)}
        />
        <button
          className="rounded-2xl bg-slate-950 px-5 py-3 font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          type="submit"
          disabled={loading || !input.trim()}
        >
          发送
        </button>
      </form>
    </aside>
  );
}

export default function App() {
  const [health, setHealth] = useState("checking");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState("");
  const [currentUser, setCurrentUser] = useState("");

  const [selectedStocks, setSelectedStocks] = useState<StockOption[]>([HOT_STOCKS[0]]);
  const [manualCode, setManualCode] = useState("");
  const [manualLoading, setManualLoading] = useState(false);
  const [manualError, setManualError] = useState("");
  const [startDate, setStartDate] = useState(oneYearAgo());
  const [endDate, setEndDate] = useState(today());
  const [activeCode, setActiveCode] = useState(HOT_STOCKS[0].code);
  const [activeTab, setActiveTab] = useState<ActiveTab>("data");

  const [records, setRecords] = useState<Record<string, StockRecord[]>>({});
  const [newsMap, setNewsMap] = useState<Record<string, StockRecord[]>>({});
  const [newsFallbackMap, setNewsFallbackMap] = useState<Record<string, boolean>>({});
  const [forecastMap, setForecastMap] = useState<Record<string, StockRecord[]>>({});
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);

  const [technicalTextMap, setTechnicalTextMap] = useState<Record<string, string>>({});
  const [forecastTextMap, setForecastTextMap] = useState<Record<string, string>>({});
  const [newsTextMap, setNewsTextMap] = useState<Record<string, string>>({});
  const [newsScoreMap, setNewsScoreMap] = useState<Record<string, number>>({});

  const [loading, setLoading] = useState(false);
  const [technicalLoading, setTechnicalLoading] = useState(false);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState("");
  const [pdfCache, setPdfCache] = useState<Record<string, PdfCacheItem>>({});
  const [historyOpen, setHistoryOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [stockManageOpen, setStockManageOpen] = useState(false);

  useEffect(() => {
    getHealth()
      .then((payload) => setHealth(payload.status))
      .catch(() => setHealth("offline"));
  }, []);

  useEffect(() => {
    if (!currentUser) {
      setHistoryItems([]);
      return;
    }
    getUserHistory(currentUser)
      .then(setHistoryItems)
      .catch(() => setHistoryItems([]));
  }, [currentUser]);

  async function handleAuthSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthLoading(true);
    setAuthMessage("");
    try {
      if (authMode === "register") {
        const payload = await register(username.trim(), password);
        setAuthMessage(payload.message);
        if (payload.success) {
          setAuthMode("login");
        }
        return;
      }

      const payload = await login(username.trim(), password);
      if (!payload.success) {
        setAuthMessage("用户名或密码错误。");
        return;
      }

      setCurrentUser(username.trim());
      setAuthMessage("");
    } catch (err) {
      setAuthMessage(err instanceof Error ? err.message : "认证失败。");
    } finally {
      setAuthLoading(false);
    }
  }

  async function addManualStock() {
    const symbol = manualCode.trim();
    if (!symbol) {
      return;
    }
    if (selectedStocks.some((item) => item.code === symbol)) {
      setManualError("该股票已经在当前列表中。");
      return;
    }
    if (selectedStocks.length >= 3) {
      setManualError("最多同时分析 3 只股票。");
      return;
    }

    setManualLoading(true);
    setManualError("");
    try {
      const name = await getStockName(symbol);
      setSelectedStocks((current) => [...current, { code: symbol, name }]);
      setActiveCode(symbol);
      setManualCode("");
    } catch (err) {
      setManualError(err instanceof Error ? err.message : "股票代码校验失败。");
    } finally {
      setManualLoading(false);
    }
  }

  async function loadAnalysis() {
    setLoading(true);
    setError("");
    try {
      const loaded = await Promise.all(
        selectedStocks.map(async (stock) => {
          const data = await getStockData(stock.code, startDate, endDate);
          const newsPayload = await getStockNews(stock.code, stock.name, 10);
          const forecastPayload = data.length >= 30 ? await getForecast(data, 7) : { records: [] };
          if (currentUser) {
            await logHistory(currentUser, stock.name, stock.code);
          }
          return {
            code: stock.code,
            data,
            news: newsPayload.records,
            isFallback: newsPayload.is_fallback,
            forecast: forecastPayload.records,
          };
        }),
      );

      const nextRecords: Record<string, StockRecord[]> = {};
      const nextNews: Record<string, StockRecord[]> = {};
      const nextFallback: Record<string, boolean> = {};
      const nextForecast: Record<string, StockRecord[]> = {};

      for (const item of loaded) {
        nextRecords[item.code] = item.data;
        nextNews[item.code] = item.news;
        nextFallback[item.code] = item.isFallback;
        nextForecast[item.code] = item.forecast;
      }

      setRecords(nextRecords);
      setNewsMap(nextNews);
      setNewsFallbackMap(nextFallback);
      setForecastMap(nextForecast);

      if (!nextRecords[activeCode]) {
        setActiveCode(selectedStocks[0]?.code ?? "");
      }
      if (currentUser) {
        const history = await getUserHistory(currentUser);
        setHistoryItems(history);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析加载失败。");
    } finally {
      setLoading(false);
    }
  }

  function toggleStock(option: StockOption) {
    const exists = selectedStocks.some((item) => item.code === option.code);
    if (exists) {
      const next = selectedStocks.filter((item) => item.code !== option.code);
      setSelectedStocks(next);
      if (activeCode === option.code && next.length > 0) {
        setActiveCode(next[0].code);
      }
      return;
    }
    if (selectedStocks.length >= 3) {
      setManualError("最多同时分析 3 只股票。");
      return;
    }
    setSelectedStocks((current) => [...current, option]);
  }

  function removeSelectedStock(code: string) {
    setSelectedStocks((current) => {
      const next = current.filter((item) => item.code !== code);
      if (activeCode === code && next.length > 0) {
        setActiveCode(next[0].code);
      }
      return next.length > 0 ? next : current;
    });
    setStockManageOpen(false);
  }

  function handleLogout() {
    if (!window.confirm("确认退出登录吗？")) {
      return;
    }
    setCurrentUser("");
    setPassword("");
    setAuthMessage("");
    setRecords({});
    setNewsMap({});
    setNewsFallbackMap({});
    setForecastMap({});
    setTechnicalTextMap({});
    setForecastTextMap({});
    setNewsTextMap({});
    setNewsScoreMap({});
    setHistoryItems([]);
    setPdfCache({});
    setSelectedStocks([HOT_STOCKS[0]]);
    setActiveCode(HOT_STOCKS[0].code);
    setActiveTab("data");
  }

  async function handleDeleteHistoryItem(itemId: number) {
    try {
      await deleteHistoryItem(itemId);
      setHistoryItems((current) => current.filter((item) => item.id !== itemId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除历史记录失败。");
    }
  }

  async function handleClearHistory() {
    if (!window.confirm("确认清空全部历史记录吗？")) {
      return;
    }
    try {
      await deleteAllUserHistory(currentUser);
      setHistoryItems([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "清空历史记录失败。");
    }
  }

  async function handleGeneratePdf() {
    const activeStock = selectedStocks.find((item) => item.code === activeCode);
    const hasAnalysis = activeStock ? (records[activeStock.code] ?? []).length > 0 : false;
    if (!activeStock || !hasAnalysis) {
      setError("请先点击“生成分析报告”，并等待当前股票分析结果加载完成后，再生成或下载 PDF。");
      return false;
    }

    setPdfLoading(true);
    setError("");
    try {
      const payload = await generatePdfReport(activeStock.code, activeStock.name, startDate, endDate);
      const item = { filename: payload.filename, blob: payload.bytes };
      const cacheKey = `${activeStock.code}:${startDate}:${endDate}`;
      downloadPdf(item);
      setPdfCache((current) => ({ ...current, [cacheKey]: item }));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF 下载失败。");
    } finally {
      setPdfLoading(false);
    }
  }

  const activeStock = selectedStocks.find((item) => item.code === activeCode) ?? selectedStocks[0];
  const activeRecords = activeStock ? records[activeStock.code] ?? [] : [];
  const activeNews = activeStock ? newsMap[activeStock.code] ?? [] : [];
  const activeForecast = activeStock ? forecastMap[activeStock.code] ?? [] : [];
  const latestRecord = activeRecords.length > 0 ? activeRecords[activeRecords.length - 1] : undefined;
  const currentPdfCacheKey = activeStock ? `${activeStock.code}:${startDate}:${endDate}` : "";
  const currentPdf = currentPdfCacheKey ? pdfCache[currentPdfCacheKey] : undefined;
  const comparisonSeries = selectedStocks.map((stock) => ({ name: stock.name, records: records[stock.code] ?? [] }));
  const metrics = calculateMetrics(activeRecords);
  const sentimentScore = activeStock ? newsScoreMap[activeStock.code] ?? 50 : 50;
  const canGeneratePdf = Boolean(activeStock && activeRecords.length > 0);

  async function runTechnicalAnalysis() {
    if (!activeStock || activeRecords.length < 2) {
      return;
    }
    const prompt = buildTechnicalPrompt(activeStock.name, activeRecords, comparisonSeries);
    if (!prompt) {
      return;
    }
    setTechnicalLoading(true);
    try {
      setTechnicalTextMap((current) => ({ ...current, [activeStock.code]: "" }));
      let content = "";
      for await (const chunk of streamAssistant([{ role: "user", content: prompt }], 0.8)) {
        content += chunk;
        setTechnicalTextMap((current) => ({ ...current, [activeStock.code]: content }));
      }
    } catch (err) {
      setTechnicalTextMap((current) => ({
        ...current,
        [activeStock.code]: err instanceof Error ? err.message : "技术分析生成失败。",
      }));
    } finally {
      setTechnicalLoading(false);
    }
  }

  async function runForecastAnalysis() {
    if (!activeStock || !activeForecast.length) {
      return;
    }
    const prompt = buildForecastPrompt(activeStock.name, activeForecast);
    if (!prompt) {
      return;
    }
    setForecastLoading(true);
    try {
      setForecastTextMap((current) => ({ ...current, [activeStock.code]: "" }));
      let content = "";
      for await (const chunk of streamAssistant([{ role: "user", content: prompt }], 0.8)) {
        content += chunk;
        setForecastTextMap((current) => ({ ...current, [activeStock.code]: content }));
      }
    } catch (err) {
      setForecastTextMap((current) => ({
        ...current,
        [activeStock.code]: err instanceof Error ? err.message : "趋势解读生成失败。",
      }));
    } finally {
      setForecastLoading(false);
    }
  }

  async function runNewsAnalysis() {
    if (!activeStock || !activeNews.length) {
      return;
    }
    const prompt = buildSentimentPrompt(
      activeStock.name,
      activeNews,
      activeRecords,
      metrics,
      newsFallbackMap[activeStock.code] ?? false,
    );
    if (!prompt) {
      return;
    }
    setNewsLoading(true);
    try {
      let content = "";
      for await (const chunk of streamAssistant([{ role: "user", content: prompt }], 0.6)) {
        content += chunk;
        const parsedPartial = parseSentiment(content);
        setNewsTextMap((current) => ({ ...current, [activeStock.code]: parsedPartial.analysis }));
        if (parsedPartial.score != null) {
          setNewsScoreMap((current) => ({ ...current, [activeStock.code]: parsedPartial.score as number }));
        }
      }
      const parsed = parseSentiment(content);
      setNewsTextMap((current) => ({ ...current, [activeStock.code]: parsed.analysis }));
      if (parsed.score != null) {
        setNewsScoreMap((current) => ({ ...current, [activeStock.code]: parsed.score as number }));
      }
    } catch (err) {
      setNewsTextMap((current) => ({
        ...current,
        [activeStock.code]: err instanceof Error ? err.message : "舆情分析生成失败。",
      }));
    } finally {
      setNewsLoading(false);
    }
  }

  if (!currentUser) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_#fee2e2,_#f8fafc_42%,_#e2e8f0)] px-6">
        <div className="grid w-full max-w-6xl gap-10 rounded-[40px] bg-white/90 p-8 shadow-2xl ring-1 ring-slate-200 backdrop-blur lg:grid-cols-[1.05fr_0.95fr]">
          <section className="rounded-[32px] bg-slate-950 px-8 py-10 text-white">
            <h1 className="mt-8 text-5xl font-semibold leading-tight">新能源车股票分析系统</h1>
            <p className="mt-5 max-w-xl text-sm leading-8 text-slate-300">登录后进入股票分析工作台。</p>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <MetricCard label="后端状态" value={health === "ok" ? "在线" : health === "checking" ? "检查中" : "离线"} />
              <MetricCard label="数据库" value="PostgreSQL" />
              <MetricCard label="缓存策略" value="增量存储" />
              <MetricCard label="报告能力" value="PDF + AI" />
            </div>
          </section>

          <section className="flex items-center">
            <form className="w-full space-y-5" onSubmit={handleAuthSubmit}>
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                  {authMode === "login" ? "Sign In" : "Create Account"}
                </p>
                <h2 className="mt-3 text-3xl font-semibold text-slate-900">
                  {authMode === "login" ? "登录后进入分析工作台" : "先创建一个账户"}
                </h2>
                <p className="mt-3 text-sm leading-7 text-slate-500">
                  当前版本保留通用 Agent、技术分析、趋势预测、新闻舆情和 PDF 报告能力。
                </p>
              </div>

              <label className="block">
                <span className="text-sm font-medium text-slate-700">用户名</span>
                <input
                  className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                />
              </label>

              <label className="block">
                <span className="text-sm font-medium text-slate-700">密码</span>
                <input
                  className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </label>

              <button
                className="inline-flex w-full items-center justify-center rounded-2xl bg-red-500 px-4 py-3 font-semibold text-white transition hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-60"
                type="submit"
                disabled={authLoading || !username.trim() || !password}
              >
                {authLoading ? "提交中..." : authMode === "login" ? "登录" : "注册"}
              </button>

              {authMessage ? <p className="text-sm text-red-600">{authMessage}</p> : null}

              <button
                className="text-sm font-medium text-slate-500 underline-offset-4 hover:text-slate-900 hover:underline"
                type="button"
                onClick={() => setAuthMode((current) => (current === "login" ? "register" : "login"))}
              >
                {authMode === "login" ? "还没有账号？去注册" : "已有账号？返回登录"}
              </button>
            </form>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f5f5f7] text-slate-900">
      <div className={`mx-auto grid max-w-[1680px] gap-6 px-6 py-8 ${sidebarCollapsed ? "lg:grid-cols-[72px_minmax(0,1fr)]" : "lg:grid-cols-[320px_minmax(0,1fr)]"}`}>
        <aside className="rounded-[30px] border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              {!sidebarCollapsed ? (
                <>
                  <h1 className="mt-3 text-3xl font-semibold leading-tight text-slate-950">选股控制台</h1>
                  <p className="mt-3 text-sm leading-7 text-slate-500">左边只负责选股、时间范围和触发分析。右侧上方是通用 Agent，下面是四个功能页。</p>
                </>
              ) : null}
            </div>
            <button
              className={`rounded-full border border-slate-200 px-3 py-2 text-sm text-slate-600 transition hover:border-slate-400 hover:text-slate-900 ${sidebarCollapsed ? "hidden" : ""}`}
              onClick={() => setSidebarCollapsed(true)}
            >
              {sidebarCollapsed ? "展开" : "收起"}
            </button>
          </div>

          {sidebarCollapsed ? (
            <div className="mt-4 space-y-3">
              <button
                className="w-full rounded-2xl border border-slate-200 px-3 py-3 text-sm font-medium text-slate-700"
                onClick={() => setSidebarCollapsed(false)}
              >
                展开侧边栏
              </button>
              <button className="w-full rounded-2xl bg-red-500 px-3 py-3 text-sm font-semibold text-white" onClick={loadAnalysis} disabled={loading || selectedStocks.length === 0}>
                分析
              </button>
            </div>
          ) : (
            <>
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Backend</p>
            <p className="mt-2 text-lg font-medium">{health === "ok" ? "在线" : health === "checking" ? "检查中" : "离线"}</p>
            <p className="mt-2 text-sm text-slate-500">当前登录用户：{currentUser}</p>
          </div>

          <div className="mt-6 space-y-4">
            <label className="block">
              <span className="text-sm font-medium text-slate-700">开始日期</span>
              <input
                className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2"
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">结束日期</span>
              <input
                className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2"
                type="date"
                value={endDate}
                onChange={(event) => setEndDate(event.target.value)}
              />
            </label>
          </div>

          <div className="mt-6">
            <p className="text-sm font-medium text-slate-700">热门股票（最多 3 只）</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {HOT_STOCKS.map((stock) => {
                const active = selectedStocks.some((item) => item.code === stock.code);
                return (
                  <button
                    key={stock.code}
                    className={`rounded-full px-3 py-2 text-sm transition ${active ? "bg-red-500 text-white" : "bg-slate-100 text-slate-700"}`}
                    onClick={() => toggleStock(stock)}
                  >
                    {stock.name}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-slate-200 p-4">
            <p className="text-sm font-medium text-slate-700">手动添加股票代码</p>
            <div className="mt-3 flex gap-2">
              <input
                className="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2"
                placeholder="例如 002594"
                value={manualCode}
                onChange={(event) => setManualCode(event.target.value)}
              />
              <button
                className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={addManualStock}
                disabled={manualLoading || !manualCode.trim()}
              >
                {manualLoading ? "校验中" : "添加"}
              </button>
            </div>
            {manualError ? <p className="mt-2 text-sm text-red-600">{manualError}</p> : null}
          </div>

          <button
            className="mt-6 inline-flex w-full items-center justify-center rounded-[24px] bg-red-500 px-4 py-4 text-base font-semibold text-white shadow-sm transition hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={loadAnalysis}
            disabled={loading || selectedStocks.length === 0}
          >
            {loading ? "正在加载分析..." : "生成分析报告"}
          </button>

          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
            </>
          )}
        </aside>

        <main className="space-y-6">
          <section className="relative rounded-[30px] border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Workspace</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-950">分析工作台</h2>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-slate-100 px-3 py-2 text-sm text-slate-600">{currentUser}</span>
                <button className="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50" onClick={() => setHistoryOpen((current) => !current)}>
                  历史
                </button>
                <button className="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50" onClick={handleLogout}>
                  退出
                </button>
              </div>
            </div>
            {historyOpen ? (
              <>
                <button className="fixed inset-0 z-10 cursor-default" onClick={() => setHistoryOpen(false)} aria-label="close history" />
                <div className="absolute right-5 top-20 z-20 w-[360px] rounded-[24px] border border-slate-200 bg-white p-4 shadow-2xl">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-lg font-semibold text-slate-950">历史记录</h3>
                    {historyItems.length > 0 ? (
                      <button className="text-sm text-red-500 transition hover:text-red-600" onClick={handleClearHistory}>
                        清空
                      </button>
                    ) : null}
                  </div>
                  <div className="mt-4 max-h-[360px] space-y-2 overflow-y-auto">
                    {historyItems.length === 0 ? (
                      <p className="text-sm text-slate-500">还没有历史记录。</p>
                    ) : (
                      historyItems.map((item) => (
                        <div key={item.id} className="flex items-start justify-between gap-2 rounded-xl bg-slate-50 px-3 py-3 text-sm">
                          <button className="min-w-0 flex-1 text-left" onClick={() => { setActiveCode(item.stock_code); setHistoryOpen(false); }}>
                            <div className="font-medium text-slate-800">
                              {item.stock_name} ({item.stock_code})
                            </div>
                            <div className="mt-1 text-xs text-slate-500">{item.visit_time_str}</div>
                          </button>
                          <button className="rounded-lg px-2 py-1 text-red-500 transition hover:bg-red-50" onClick={() => handleDeleteHistoryItem(item.id)}>
                            删除
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </>
            ) : null}
          </section>

          <AgentPanel
            currentUser={currentUser}
            selectedStocks={selectedStocks}
            activeCode={activeCode}
            startDate={startDate}
            endDate={endDate}
            records={records}
            pdfCache={pdfCache}
            onRequestPdf={handleGeneratePdf}
          />

          <section className="rounded-[30px] border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Current Stock</p>
                <h2 className="mt-2 text-3xl font-semibold text-slate-950">
                  {activeStock ? `${activeStock.name} (${activeStock.code})` : "未选择股票"}
                </h2>
                <p className="mt-2 text-sm text-slate-500">注：如果删除某股票后重新选择，需要重新点击“生成分析报告”刷新结果。</p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                {selectedStocks.length > 1 ? (
                  <button
                    className="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                    onClick={() => setStockManageOpen((current) => !current)}
                  >
                    {stockManageOpen ? "完成管理" : "管理股票"}
                  </button>
                ) : null}
                {selectedStocks.map((stock) => (
                  <div
                    key={stock.code}
                    className={`flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition ${
                      stock.code === activeCode ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    <button onClick={() => setActiveCode(stock.code)}>{stock.name}</button>
                    {selectedStocks.length > 1 && stockManageOpen ? (
                      <button
                        className={`rounded-full px-2 py-0.5 text-xs ${stock.code === activeCode ? "bg-white/15 text-white" : "bg-white text-red-500"}`}
                        onClick={() => removeSelectedStock(stock.code)}
                      >
                        删除
                      </button>
                    ) : null}
                  </div>
                ))}
                <button
                  className="rounded-full bg-red-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-60"
                  onClick={handleGeneratePdf}
                  disabled={pdfLoading || !canGeneratePdf}
                >
                  {pdfLoading ? "生成中..." : currentPdf ? "下载当前 PDF" : "生成 / 下载 PDF"}
                </button>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-4">
            <MetricCard label="已选股票" value={String(selectedStocks.length)} />
            <MetricCard label="当前记录数" value={String(activeRecords.length)} />
            <MetricCard label="分析周期" value={`${startDate} ~ ${endDate}`} />
            <MetricCard label="PDF 状态" value={currentPdf ? "已缓存" : "未生成"} />
          </section>

          <section className="rounded-[30px] border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap gap-2">
              {[
                ["data", "📊 基础数据"],
                ["technical", "📈 技术 & AI"],
                ["forecast", "🔮 趋势预测"],
                ["news", "📰 舆情 & 情绪"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                    activeTab === key ? "bg-red-500 text-white" : "bg-slate-100 text-slate-700"
                  }`}
                  onClick={() => setActiveTab(key as ActiveTab)}
                >
                  {label}
                </button>
              ))}
            </div>
          </section>

          {activeTab === "data" ? (
            <section className="rounded-[30px] border border-slate-200 bg-white p-6 shadow-sm">
              <SectionHeader eyebrow="Data" title="基础数据" description="这里负责基础概览和历史行情表，不调用通用 Agent。" />
              {activeRecords.length === 0 ? (
                <EmptyState text="先在左侧点击红色“生成分析报告”，然后再查看基础数据。" />
              ) : (
                <div className="space-y-5">
                  <div className="grid gap-4 md:grid-cols-3">
                    <MetricCard label="最新收盘价" value={formatMetric(getNumber(latestRecord, "收盘"))} />
                    <MetricCard
                      label="最高价（区间）"
                      value={formatMetric(Math.max(...activeRecords.map((item) => getNumber(item, "最高") ?? Number.NEGATIVE_INFINITY)))}
                    />
                    <MetricCard
                      label="最低价（区间）"
                      value={formatMetric(Math.min(...activeRecords.map((item) => getNumber(item, "最低") ?? Number.POSITIVE_INFINITY)))}
                    />
                  </div>
                  <RecordTable records={activeRecords} />
                </div>
              )}
            </section>
          ) : null}

          {activeTab === "technical" ? (
            <section className="rounded-[30px] border border-slate-200 bg-white p-6 shadow-sm">
              <SectionHeader
                eyebrow="Technical"
                title="技术与 AI"
                description="技术面图表、夏普率、最大回撤、年化波动率，以及技术分析提示词生成的 AI 报告。"
              />
              {activeRecords.length === 0 ? (
                <EmptyState text="先生成当前股票的分析数据，再查看技术页。" />
              ) : (
                <div className="space-y-6">
                  <div className="max-h-[980px] space-y-5 overflow-y-auto pr-2">
                    <div className="grid gap-4 md:grid-cols-3">
                      <MetricCard label="夏普比率" value={formatMetric(metrics.sharpe)} />
                      <MetricCard label="最大回撤" value={formatMetric(metrics.maxDrawdown == null ? null : metrics.maxDrawdown * 100, 2, "%")} />
                      <MetricCard label="年化波动率" value={formatMetric(metrics.volatility == null ? null : metrics.volatility * 100, 2, "%")} />
                    </div>
                    <Suspense fallback={<ChartLoading />}>
                      <KLineChart records={activeRecords} />
                    </Suspense>
                    <Suspense fallback={<ChartLoading />}>
                      <ReturnChart records={activeRecords} />
                    </Suspense>
                    <Suspense fallback={<ChartLoading />}>
                      <ComparisonChart series={comparisonSeries} />
                    </Suspense>
                  </div>
                  <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
                    <h4 className="text-2xl font-semibold text-slate-950">DeepSeek 技术分析师</h4>
                    <div className="mt-4 rounded-2xl bg-blue-50 px-4 py-4 text-sm leading-7 text-blue-700">
                      点击下方按钮，按 `assistant.py` 的技术提示词生成分析报告。
                    </div>
                    <button
                      className="mt-4 w-full rounded-2xl border border-slate-200 px-4 py-3 text-base font-medium text-slate-800 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                      onClick={runTechnicalAnalysis}
                      disabled={technicalLoading}
                    >
                      {technicalLoading ? "生成中..." : "生成技术分析报告"}
                    </button>
                    <MarkdownPanel
                      content={activeStock ? technicalTextMap[activeStock.code] ?? "" : ""}
                      emptyText="尚未生成技术分析。"
                      className="mt-4 min-h-[320px] rounded-[24px] bg-slate-50 p-4 text-sm leading-7 text-slate-700"
                    />
                  </div>
                </div>
              )}
            </section>
          ) : null}

          {activeTab === "forecast" ? (
            <section className="rounded-[30px] border border-slate-200 bg-white p-6 shadow-sm">
              <SectionHeader eyebrow="Forecast" title="趋势预测" description="这里专门展示预测图和趋势顾问，不走通用 Agent。" />
              {activeForecast.length === 0 ? (
                <EmptyState text="当前股票历史数据不足或还没有预测结果。" />
              ) : (
                <div className="space-y-6">
                  <div className="max-h-[980px] space-y-5 overflow-y-auto pr-2">
                    <Suspense fallback={<ChartLoading />}>
                      <ForecastChart history={activeRecords} forecast={activeForecast} />
                    </Suspense>
                  </div>
                  <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
                    <h4 className="text-2xl font-semibold text-slate-950">DeepSeek 趋势顾问</h4>
                    <div className="mt-4 rounded-2xl bg-blue-50 px-4 py-4 text-sm leading-7 text-blue-700">
                      Prophet 结果已就绪，可直接用预测提示词生成趋势解读。
                    </div>
                    <button
                      className="mt-4 w-full rounded-2xl border border-slate-200 px-4 py-3 text-base font-medium text-slate-800 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                      onClick={runForecastAnalysis}
                      disabled={forecastLoading}
                    >
                      {forecastLoading ? "生成中..." : "解读未来趋势"}
                    </button>
                    <MarkdownPanel
                      content={activeStock ? forecastTextMap[activeStock.code] ?? "" : ""}
                      emptyText="尚未生成趋势解读。"
                      className="mt-4 min-h-[320px] rounded-[24px] bg-slate-50 p-4 text-sm leading-7 text-slate-700"
                    />
                  </div>
                </div>
              )}
            </section>
          ) : null}

          {activeTab === "news" ? (
            <section className="rounded-[30px] border border-slate-200 bg-white p-6 shadow-sm">
              <SectionHeader eyebrow="News" title="舆情与情绪" description="新闻图表、新闻列表和舆情提示词分析都放在这一页。" />
              {activeNews.length === 0 ? (
                <EmptyState text="先生成分析，再查看新闻与舆情。" />
              ) : (
                <div className="space-y-6">
                  <div className="max-h-[980px] space-y-5 overflow-y-auto pr-2">
                    <Suspense fallback={<ChartLoading />}>
                      <SentimentGaugeChart score={sentimentScore} />
                    </Suspense>
                    <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
                      <div className="mb-4 rounded-2xl bg-emerald-50 px-4 py-4 text-sm text-emerald-700">
                        {newsFallbackMap[activeStock?.code ?? ""] ? "当前为行业资讯回退结果。" : `获取成功：${activeStock?.name ?? "--"} 个股资讯`}
                      </div>
                      <div className="space-y-3">
                        {activeNews.slice(0, 10).map((item, index) => {
                          const link = getNewsLink(item);
                          return (
                            <div key={index} className="rounded-2xl border border-slate-200 px-4 py-4">
                              <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
                                {String(item["发布时间"] ?? "最近资讯")}
                              </div>
                              <div className="mt-2 text-sm font-medium leading-7 text-slate-800">
                                {String(item["新闻标题"] ?? item["标题"] ?? "--")}
                              </div>
                              {link ? (
                                <a
                                  className="mt-2 inline-flex text-sm text-red-500 hover:text-red-600"
                                  href={link}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  查看原文
                                </a>
                              ) : null}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                  <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
                    <h4 className="text-2xl font-semibold text-slate-950">AI 舆情分析</h4>
                    <div className="mt-4 rounded-2xl bg-blue-50 px-4 py-4 text-sm leading-7 text-blue-700">
                      使用 `assistant.py` 中的舆情提示词生成情绪分数和分析结论。
                    </div>
                    <button
                      className="mt-4 w-full rounded-2xl bg-red-500 px-4 py-3 text-base font-semibold text-white transition hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-60"
                      onClick={runNewsAnalysis}
                      disabled={newsLoading}
                    >
                      {newsLoading ? "分析中..." : "开始 AI 分析"}
                    </button>
                    <div className="mt-4 rounded-2xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-700">
                      新闻舆情得分：{sentimentScore}
                    </div>
                    <MarkdownPanel
                      content={activeStock ? newsTextMap[activeStock.code] ?? "" : ""}
                      emptyText="尚未生成舆情分析。"
                      className="mt-4 min-h-[320px] rounded-[24px] bg-slate-50 p-4 text-sm leading-7 text-slate-700"
                    />
                  </div>
                </div>
              )}
            </section>
          ) : null}
        </main>
      </div>
    </div>
  );
}
