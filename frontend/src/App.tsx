import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  deleteHistoryItem,
  generatePdfReport,
  getForecast,
  getHealth,
  getPriceHistory,
  getStockNews,
  getUserHistory,
  logHistory,
  login,
  register,
  resolveInstrument,
} from "./lib/api";
import { ForecastPage } from "./pages/dashboard/ForecastPage";
import { HistoryPage } from "./pages/dashboard/HistoryPage";
import { MarketAnalysisPage } from "./pages/dashboard/MarketAnalysisPage";
import { OverviewPage } from "./pages/dashboard/OverviewPage";
import { PortfolioPage } from "./pages/dashboard/PortfolioPage";
import { SentimentPage } from "./pages/dashboard/SentimentPage";
import { TechnicalAnalysisPage } from "./pages/dashboard/TechnicalAnalysisPage";
import { DashboardLayout } from "./pages/dashboard/DashboardLayout";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { StockSetupPage } from "./pages/StockSetupPage";
import {
  HOT_STOCKS,
  buildContext,
  download,
  money,
  oneYearAgo,
  percent,
  pricePrefix,
  scoreMetrics,
  today,
  type PdfCacheItem,
  type SetupMarket,
  type WorkspaceTab,
} from "./lib/workspace";
import type { ForecastPoint, HistoryItem, Instrument, NewsItem, PriceBar } from "./types";

type Screen = "landing" | "auth" | "setup" | "workspace";
type AuthMode = "login" | "register";

export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [currentUser, setCurrentUser] = useState("");
  const [health, setHealth] = useState("checking");

  const [market, setMarket] = useState<SetupMarket>("cn");
  const [selectedStocks, setSelectedStocks] = useState<Instrument[]>(HOT_STOCKS.slice(0, 3));
  const [manualCode, setManualCode] = useState("");
  const [manualError, setManualError] = useState("");
  const [activeCode, setActiveCode] = useState(HOT_STOCKS[0].id);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("overview");
  const [startDate, setStartDate] = useState(oneYearAgo());
  const [endDate, setEndDate] = useState(today());
  const [loading, setLoading] = useState(false);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const [pdfStatus, setPdfStatus] = useState("");
  const [workspaceError, setWorkspaceError] = useState("");
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [recordsByCode, setRecordsByCode] = useState<Record<string, PriceBar[]>>({});
  const [forecastByCode, setForecastByCode] = useState<Record<string, ForecastPoint[]>>({});
  const [newsByCode, setNewsByCode] = useState<Record<string, NewsItem[]>>({});
  const [newsFallbackByCode, setNewsFallbackByCode] = useState<Record<string, boolean>>({});
  const [pdfCache, setPdfCache] = useState<Record<string, PdfCacheItem>>({});

  useEffect(() => {
    void getHealth().then((payload) => setHealth(payload.status)).catch(() => setHealth("offline"));
  }, []);

  useEffect(() => {
    if (!currentUser) {
      setHistoryItems([]);
      return;
    }
    void getUserHistory(currentUser).then(setHistoryItems).catch(() => setHistoryItems([]));
  }, [currentUser]);

  const filteredHotStocks = useMemo(() => {
    return HOT_STOCKS;
  }, [market]);

  const activeStock = selectedStocks.find((item) => item.id === activeCode) ?? null;
  const activeRecords = activeStock ? recordsByCode[activeStock.id] ?? [] : [];
  const activeForecast = activeStock ? forecastByCode[activeStock.id] ?? [] : [];
  const activeNews = activeStock ? newsByCode[activeStock.id] ?? [] : [];
  const activeNewsFallback = activeStock ? Boolean(newsFallbackByCode[activeStock.id]) : false;
  const latestRecord = activeRecords[activeRecords.length - 1];
  const metrics = scoreMetrics(activeRecords);
  const comparisonSeries = selectedStocks.map((item) => ({ name: item.display_name, records: recordsByCode[item.id] ?? [] }));
  const pdfKey = activeStock ? `${activeStock.id}:${startDate}:${endDate}` : "";
  const currentPdf = pdfKey ? pdfCache[pdfKey] : null;
  const analysisReady = Boolean(activeStock && activeRecords.length);

  async function refreshHistory() {
    if (!currentUser) return;
    try {
      setHistoryItems(await getUserHistory(currentUser));
    } catch {
      // noop
    }
  }

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthError("");
    if (!username.trim() || !password.trim()) {
      setAuthError("请输入用户名和密码。");
      return;
    }
    try {
      if (authMode === "register") {
        const created = await register(username.trim(), password);
        if (!created.success) {
          setAuthError(created.message || "注册失败，请稍后重试。");
          return;
        }
      }
      const result = await login(username.trim(), password);
      if (!result.success) {
        setAuthError("用户名或密码错误。");
        return;
      }
      setCurrentUser(username.trim());
      setPassword("");
      setScreen("setup");
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "认证过程出现异常。");
    }
  }

  function addPresetStock(stock: Instrument) {
    setManualError("");
    const exists = selectedStocks.some((item) => item.id === stock.id);
    if (exists) {
      setActiveCode(stock.id);
      return;
    }
    if (selectedStocks.length >= 5) {
      setManualError("最多同时关注 5 只股票。");
      return;
    }
    setSelectedStocks((current) => [...current, stock]);
    setActiveCode(stock.id);
  }

  async function addManualStock() {
    const code = manualCode.trim().toUpperCase();
    setManualError("");
    if (!code) {
      setManualError("请输入股票代码。");
      return;
    }
    const marketHint = "CN";
    try {
      const instrument = await resolveInstrument(code, marketHint);
      if (selectedStocks.some((item) => item.id === instrument.id)) {
        setManualError("该股票已在列表中。");
        return;
      }
      if (selectedStocks.length >= 5) {
        setManualError("最多同时关注 5 只股票。");
        return;
      }
      setSelectedStocks((current) => [...current, instrument]);
      setActiveCode(instrument.id);
      setManualCode("");
    } catch (error) {
      setManualError(error instanceof Error ? error.message : "股票信息获取失败。");
    }
  }

  function removeStock(code: string) {
    const next = selectedStocks.filter((item) => item.id !== code);
    setSelectedStocks(next);
    if (code === activeCode) {
      setActiveCode(next[0]?.id ?? "");
    }
  }

  async function loadAnalysis() {
    if (!selectedStocks.length) {
      setWorkspaceError("请先选择至少一只股票。");
      return false;
    }
    setLoading(true);
    setWorkspaceError("");
    try {
      const result = await Promise.all(
        selectedStocks.map(async (stock) => {
          const history = await getPriceHistory(stock, startDate, endDate);
          const resolvedInstrument =
            history.instrument.display_name === history.instrument.symbol
              ? { ...history.instrument, display_name: stock.display_name }
              : history.instrument;
          const [forecast, news] = await Promise.all([
            getForecast(history.records, 7).catch(() => ({ records: [] as ForecastPoint[] })),
            getStockNews(resolvedInstrument, 8).catch(() => ({ instrument: resolvedInstrument, records: [] as NewsItem[], meta: { provider: "", fallback_used: false } })),
          ]);
          return {
            instrument: resolvedInstrument,
            records: history.records,
            forecast: forecast.records,
            news: news.records,
            fallback: news.meta.fallback_used,
          };
        }),
      );

      const nextRecords: Record<string, PriceBar[]> = {};
      const nextForecast: Record<string, ForecastPoint[]> = {};
      const nextNews: Record<string, NewsItem[]> = {};
      const nextFallback: Record<string, boolean> = {};
      const nextSelectedStocks: Instrument[] = [];

      for (const item of result) {
        nextSelectedStocks.push(item.instrument);
        nextRecords[item.instrument.id] = item.records;
        nextForecast[item.instrument.id] = item.forecast;
        nextNews[item.instrument.id] = item.news;
        nextFallback[item.instrument.id] = item.fallback;
        if (currentUser) void logHistory(currentUser, item.instrument.display_name, item.instrument.symbol);
      }

      setSelectedStocks(nextSelectedStocks);
      setRecordsByCode(nextRecords);
      setForecastByCode(nextForecast);
      setNewsByCode(nextNews);
      setNewsFallbackByCode(nextFallback);
      if (!nextSelectedStocks.some((item) => item.id === activeCode)) {
        setActiveCode(nextSelectedStocks[0]?.id ?? "");
      }
      setActiveTab("overview");
      await refreshHistory();
      return true;
    } catch (error) {
      setWorkspaceError(error instanceof Error ? error.message : "数据加载失败。");
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function proceedToWorkspace() {
    const ok = await loadAnalysis();
    if (ok) setScreen("workspace");
  }

  async function exportPdf() {
    if (!activeStock || !activeRecords.length) return false;
    if (currentPdf) {
      setPdfStatus("已使用缓存报告，正在下载。");
      download(currentPdf);
      return true;
    }
    setPdfGenerating(true);
    setPdfStatus("正在生成 PDF 报告，请稍候...");
    setWorkspaceError("");
    try {
      const result = await generatePdfReport(activeStock, startDate, endDate);
      const item = { filename: result.filename, blob: result.bytes };
      setPdfCache((current) => ({ ...current, [pdfKey]: item }));
      setPdfStatus("报告生成完成，开始下载。");
      download(item);
      return true;
    } catch (error) {
      setPdfStatus("");
      setWorkspaceError(error instanceof Error ? error.message : "PDF 导出失败。");
      return false;
    } finally {
      setPdfGenerating(false);
    }
  }

  function logout() {
    setCurrentUser("");
    setScreen("landing");
    setActiveTab("overview");
  }

  const prefix = pricePrefix(activeStock);
  const metricItems: Array<{ label: string; value: string; hint?: string; tone?: "green" | "yellow" | "gray" }> = [
    {
      label: "最新收盘价",
      value: money(latestRecord?.close ?? null, prefix),
      hint: percent(latestRecord?.pct_change ?? null),
      tone: latestRecord?.pct_change != null && latestRecord.pct_change >= 0 ? "green" : "yellow",
    },
    { label: "区间收益率", value: percent(metrics.total), hint: "按当前分析周期计算", tone: "green" },
    { label: "年化波动率", value: percent(metrics.volatility), hint: "衡量价格波动强度", tone: "gray" },
    { label: "最大回撤", value: percent(metrics.drawdown), hint: "衡量区间下行风险", tone: "yellow" },
  ];

  function renderModule() {
    switch (activeTab) {
      case "overview":
        return <OverviewPage ready={analysisReady} activeStock={activeStock} comparisonSeries={comparisonSeries} activeNews={activeNews} latestRecord={latestRecord} />;
      case "market":
        return <MarketAnalysisPage ready={analysisReady} activeRecords={activeRecords} comparisonSeries={comparisonSeries} />;
      case "technical":
        return <TechnicalAnalysisPage ready={analysisReady} activeRecords={activeRecords} />;
      case "sentiment":
        return <SentimentPage ready={analysisReady} activeNews={activeNews} activeNewsFallback={activeNewsFallback} />;
      case "forecast":
        return <ForecastPage ready={analysisReady} history={activeRecords} forecast={activeForecast} />;
      case "portfolio":
        return <PortfolioPage currentUser={currentUser} />;
      case "history":
        return (
          <HistoryPage
            items={historyItems}
            onSetActiveCode={(code) => {
              const target = selectedStocks.find((item) => item.symbol === code);
              if (target) {
                setActiveCode(target.id);
                setActiveTab("overview");
              }
            }}
            onDelete={(id) => {
              void deleteHistoryItem(id).then(refreshHistory);
            }}
          />
        );
      default:
        return null;
    }
  }

  if (screen === "landing") {
    return <LandingPage health={health} onLogin={() => setScreen("auth")} onExplore={() => setScreen(currentUser ? "setup" : "auth")} />;
  }

  if (screen === "auth") {
    return (
      <LoginPage
        mode={authMode}
        username={username}
        password={password}
        error={authError}
        onBack={() => setScreen("landing")}
        onModeChange={setAuthMode}
        onUsernameChange={setUsername}
        onPasswordChange={setPassword}
        onSubmit={submitAuth}
      />
    );
  }

  if (screen === "setup") {
    return (
      <StockSetupPage
        currentUser={currentUser}
        market={market}
        selectedStocks={selectedStocks}
        activeCode={activeCode}
        manualCode={manualCode}
        manualError={manualError}
        startDate={startDate}
        endDate={endDate}
        loading={loading}
        workspaceError={workspaceError}
        onBack={() => setScreen("auth")}
        onProceed={() => void proceedToWorkspace()}
        onMarketChange={setMarket}
        onManualCodeChange={setManualCode}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
        onSetActiveCode={setActiveCode}
        onAddStock={addPresetStock}
        onAddManualStock={() => void addManualStock()}
        onRemoveStock={removeStock}
        hotStocks={filteredHotStocks}
      />
    );
  }

  return (
    <DashboardLayout
      currentUser={currentUser}
      health={health}
      activeTab={activeTab}
      activeStock={activeStock}
      startDate={startDate}
      endDate={endDate}
      metricItems={metricItems}
      assistantContext={buildContext({ currentUser, activeStock, selectedStocks, startDate, endDate, activeTab, records: recordsByCode, pdfCache })}
      moduleContent={renderModule()}
      onTabChange={setActiveTab}
      onBackToSetup={() => setScreen("setup")}
      onLogout={logout}
      onExportPdf={() => exportPdf()}
      exportDisabled={!activeRecords.length}
      exportLoading={pdfGenerating}
      exportStatus={pdfStatus}
      workspaceError={workspaceError}
    />
  );
}

