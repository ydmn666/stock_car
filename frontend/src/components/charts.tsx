import { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import type { StockRecord } from "../types";

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function getDate(value: unknown) {
  return typeof value === "string" ? value.slice(0, 19) : "--";
}

function ChartFrame(props: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <article className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4">
        <h4 className="text-lg font-semibold text-slate-900">{props.title}</h4>
        <p className="mt-1 text-sm text-slate-500">{props.subtitle}</p>
      </div>
      {props.children}
    </article>
  );
}

const plotConfig: any = {
  displaylogo: false,
  responsive: true,
  modeBarButtonsToRemove: ["lasso2d", "select2d"],
};

export function KLineChart(props: { records: StockRecord[] }) {
  const rows = useMemo(
    () =>
      props.records
        .map((record) => ({
          date: getDate(record["日期"]),
          open: toNumber(record["开盘"]),
          close: toNumber(record["收盘"]),
          high: toNumber(record["最高"]),
          low: toNumber(record["最低"]),
        }))
        .filter((item) => item.open != null && item.close != null && item.high != null && item.low != null),
    [props.records],
  );

  if (!rows.length) {
    return null;
  }

  const closes = rows.map((item) => item.close as number);
  const ma = (windowSize: number) =>
    closes.map((_, index) => {
      const slice = closes.slice(Math.max(0, index - windowSize + 1), index + 1);
      return slice.reduce((sum, value) => sum + value, 0) / slice.length;
    });

  return (
    <ChartFrame title="股价走势（K线 + 均线）" subtitle="支持 hover 查看 OHLC 数值，交互方式按股票软件习惯处理。">
      <Plot
        className="w-full"
        data={[
          {
            type: "candlestick",
            x: rows.map((item) => item.date),
            open: rows.map((item) => item.open as number),
            close: rows.map((item) => item.close as number),
            high: rows.map((item) => item.high as number),
            low: rows.map((item) => item.low as number),
            name: "K线",
            increasing: { line: { color: "#ef4444" } },
            decreasing: { line: { color: "#0f766e" } },
          },
          {
            type: "scatter",
            mode: "lines",
            x: rows.map((item) => item.date),
            y: ma(5),
            name: "MA5",
            line: { color: "#f59e0b", width: 1.8 },
          },
          {
            type: "scatter",
            mode: "lines",
            x: rows.map((item) => item.date),
            y: ma(20),
            name: "MA20",
            line: { color: "#2563eb", width: 1.8 },
          },
        ] as any}
        layout={{
          autosize: true,
          height: 520,
          paper_bgcolor: "#f8fafc",
          plot_bgcolor: "#f8fafc",
          margin: { l: 48, r: 24, t: 16, b: 32 },
          hovermode: "x unified",
          legend: { orientation: "h", x: 0.7, y: 1.08 },
          xaxis: { rangeslider: { visible: true } },
          yaxis: { title: { text: "价格" }, fixedrange: false },
        }}
        config={plotConfig}
        useResizeHandler
      />
    </ChartFrame>
  );
}

export function ReturnChart(props: { records: StockRecord[] }) {
  const rows = useMemo(
    () =>
      props.records
        .map((record) => ({
          date: getDate(record["日期"]),
          close: toNumber(record["收盘"]),
        }))
        .filter((item) => item.close != null),
    [props.records],
  );
  if (!rows.length) {
    return null;
  }

  const base = rows[0].close as number;
  const values = rows.map((item) => (((item.close as number) - base) / base) * 100);

  return (
    <ChartFrame title="区间收益率" subtitle="鼠标悬停即可查看任意日期的累计收益率。">
      <Plot
        className="w-full"
        data={[
          {
            type: "scatter",
            mode: "lines",
            x: rows.map((item) => item.date),
            y: values,
            name: "累计收益率",
            line: { color: "#2563eb", width: 2.5 },
            fill: "tozeroy",
            fillcolor: "rgba(37,99,235,0.12)",
          },
        ] as any}
        layout={{
          autosize: true,
          height: 360,
          paper_bgcolor: "#f8fafc",
          plot_bgcolor: "#f8fafc",
          margin: { l: 48, r: 24, t: 16, b: 32 },
          hovermode: "x unified",
          yaxis: { ticksuffix: "%", zeroline: true, zerolinecolor: "#94a3b8" },
        }}
        config={plotConfig}
        useResizeHandler
      />
    </ChartFrame>
  );
}

export function ComparisonChart(props: { series: Array<{ name: string; records: StockRecord[] }> }) {
  const palette = ["#ef4444", "#0f766e", "#7c3aed"];
  const traces = props.series
    .map((item, index) => {
      const rows = item.records
        .map((record) => ({
          date: getDate(record["日期"]),
          close: toNumber(record["收盘"]),
        }))
        .filter((row) => row.close != null);
      if (rows.length < 2) {
        return null;
      }
      const base = rows[0].close as number;
      return {
        type: "scatter" as const,
        mode: "lines",
        x: rows.map((row) => row.date),
        y: rows.map((row) => (((row.close as number) - base) / base) * 100),
        name: item.name,
        line: { width: 2.4, color: palette[index % palette.length] },
      };
    })
    .filter(Boolean);

  if (traces.length < 2) {
    return null;
  }

  return (
    <ChartFrame title="多股收益对比" subtitle="同区间收益率对比，hover 可查看每只股票在同一时点的表现。">
      <Plot
        className="w-full"
        data={traces as any}
        layout={{
          autosize: true,
          height: 380,
          paper_bgcolor: "#f8fafc",
          plot_bgcolor: "#f8fafc",
          margin: { l: 48, r: 24, t: 16, b: 32 },
          hovermode: "x unified",
          legend: { orientation: "h" },
          yaxis: { ticksuffix: "%", zeroline: true, zerolinecolor: "#94a3b8" },
        }}
        config={plotConfig}
        useResizeHandler
      />
    </ChartFrame>
  );
}

export function ForecastChart(props: { history: StockRecord[]; forecast: StockRecord[] }) {
  const historyRows = props.history
    .map((record) => ({
      date: getDate(record["日期"]),
      close: toNumber(record["收盘"]),
    }))
    .filter((item) => item.close != null);
  const forecastRows = props.forecast
    .map((record) => ({
      date: getDate(record["ds"]),
      yhat: toNumber(record["yhat"]),
      upper: toNumber(record["yhat_upper"]),
      lower: toNumber(record["yhat_lower"]),
    }))
    .filter((item) => item.yhat != null && item.upper != null && item.lower != null);

  if (!historyRows.length || !forecastRows.length) {
    return null;
  }

  const futureRows = forecastRows.slice(-7);

  return (
    <ChartFrame title="趋势预测" subtitle="预测区间、历史收盘和未来 7 天预测都支持 hover。">
      <Plot
        className="w-full"
        data={[
          {
            type: "scatter",
            mode: "lines",
            x: futureRows.map((item) => item.date),
            y: futureRows.map((item) => item.upper),
            line: { width: 0 },
            hoverinfo: "skip",
            showlegend: false,
          },
          {
            type: "scatter",
            mode: "lines",
            x: futureRows.map((item) => item.date),
            y: futureRows.map((item) => item.lower),
            line: { width: 0 },
            fill: "tonexty",
            fillcolor: "rgba(37,99,235,0.18)",
            name: "预测区间",
          },
          {
            type: "scatter",
            mode: "lines",
            x: historyRows.map((item) => item.date),
            y: historyRows.map((item) => item.close),
            name: "历史收盘",
            line: { color: "#111827", width: 2.4 },
          },
          {
            type: "scatter",
            mode: "lines+markers",
            x: futureRows.map((item) => item.date),
            y: futureRows.map((item) => item.yhat),
            name: "未来预测",
            line: { color: "#dc2626", width: 2.8 },
            marker: { color: "#dc2626", size: 7 },
          },
        ] as any}
        layout={{
          autosize: true,
          height: 420,
          paper_bgcolor: "#f8fafc",
          plot_bgcolor: "#f8fafc",
          margin: { l: 48, r: 24, t: 16, b: 32 },
          hovermode: "x unified",
          legend: { orientation: "h" },
          yaxis: { title: { text: "价格" } },
        }}
        config={plotConfig}
        useResizeHandler
      />
    </ChartFrame>
  );
}

export function SentimentGaugeChart(props: { score: number }) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    const target = Math.max(0, Math.min(100, props.score));
    let frame = 0;
    const start = displayScore;
    const diff = target - start;
    const timer = window.setInterval(() => {
      frame += 1;
      const next = start + diff * Math.min(frame / 18, 1);
      setDisplayScore(next);
      if (frame >= 18) {
        window.clearInterval(timer);
      }
    }, 24);
    return () => window.clearInterval(timer);
  }, [props.score]);

  const angle = 180 - (displayScore / 100) * 180;
  const radius = 92;
  const centerX = 160;
  const centerY = 160;
  const pointerX = centerX + Math.cos((Math.PI / 180) * angle) * radius;
  const pointerY = centerY - Math.sin((Math.PI / 180) * angle) * radius;
  const color = displayScore < 40 ? "#ef4444" : displayScore < 60 ? "#f59e0b" : "#16a34a";

  return (
    <ChartFrame title="市场情绪评分" subtitle="评分指针会根据 AI 返回结果动态跳动。">
      <div className="flex justify-center">
        <svg viewBox="0 0 320 220" className="h-[240px] w-full max-w-[440px]">
          <path d="M 68 160 A 92 92 0 0 1 126 80" fill="none" stroke="#fee2e2" strokeWidth="22" strokeLinecap="round" />
          <path d="M 126 80 A 92 92 0 0 1 194 80" fill="none" stroke="#fef3c7" strokeWidth="22" strokeLinecap="round" />
          <path d="M 194 80 A 92 92 0 0 1 252 160" fill="none" stroke="#dcfce7" strokeWidth="22" strokeLinecap="round" />
          <line x1={centerX} y1={centerY} x2={pointerX} y2={pointerY} stroke={color} strokeWidth="6" strokeLinecap="round" />
          <circle cx={centerX} cy={centerY} r="10" fill={color} />
          <text x="146" y="128" fill="#111827" fontSize="34" fontWeight="700">
            {Math.round(displayScore)}
          </text>
          <text x="48" y="192" fill="#64748b" fontSize="14">
            偏弱
          </text>
          <text x="146" y="56" fill="#64748b" fontSize="14">
            中性
          </text>
          <text x="236" y="192" fill="#64748b" fontSize="14">
            偏强
          </text>
        </svg>
      </div>
    </ChartFrame>
  );
}

export function NewsHeatChart(props: { records: StockRecord[] }) {
  const counts = new Map<string, number>();
  for (const record of props.records) {
    const key = getDate(record["发布时间"]).slice(0, 10);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const entries = [...counts.entries()].slice(-10);
  if (!entries.length) {
    return null;
  }

  return (
    <ChartFrame title="新闻热度" subtitle="新闻数量按日期分布，支持 hover 查看当天数量。">
      <Plot
        className="w-full"
        data={[
          {
            type: "bar",
            x: entries.map((item) => item[0]),
            y: entries.map((item) => item[1]),
            marker: { color: "#f97316", line: { color: "#ea580c", width: 1 } },
            hovertemplate: "%{x}<br>新闻数：%{y}<extra></extra>",
            name: "新闻热度",
          },
        ] as any}
        layout={{
          autosize: true,
          height: 320,
          paper_bgcolor: "#f8fafc",
          plot_bgcolor: "#f8fafc",
          margin: { l: 48, r: 24, t: 16, b: 32 },
        }}
        config={plotConfig}
        useResizeHandler
      />
    </ChartFrame>
  );
}
