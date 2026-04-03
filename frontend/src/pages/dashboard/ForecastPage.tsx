import { ForecastChart } from "../../components/charts";
import { ChartCarousel } from "../../components/dashboard/ChartCarousel";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import { money, percent } from "../../lib/workspace";
import type { ForecastPoint, PriceBar } from "../../types";

type ForecastPageProps = {
  ready: boolean;
  history: PriceBar[];
  forecast: ForecastPoint[];
};

function MetricCard(props: { label: string; value: string; hint: string; tone?: "green" | "yellow" | "gray" }) {
  const toneClass =
    props.tone === "green"
      ? "text-[var(--color-profit)]"
      : props.tone === "yellow"
        ? "text-[var(--color-risk)]"
        : "text-[var(--color-text-strong)]";

  return (
    <div className="glass-panel rounded-[24px] px-5 py-4">
      <p className="text-sm text-[var(--color-text-soft)]">{props.label}</p>
      <p className={`mt-3 break-all text-[1.65rem] font-semibold leading-tight xl:text-[1.85rem] ${toneClass}`}>{props.value}</p>
      <p className="mt-2 text-sm text-[var(--color-text-muted)]">{props.hint}</p>
    </div>
  );
}

function ScenarioPanel(props: {
  targetPrice: number | null;
  lowerPrice: number | null;
  upperPrice: number | null;
  lastClose: number | null;
  changePct: number | null;
}) {
  const direction =
    props.changePct == null ? "等待预测结果" : props.changePct >= 0 ? "短期偏强" : "短期承压";
  const tone = props.changePct == null ? "gray" : props.changePct >= 0 ? "green" : "yellow";

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
      <div className="glass-panel rounded-[24px] p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-soft)]">预测结论</p>
        <h4 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">{direction}</h4>
        <p className="mt-3 text-sm leading-7 text-[var(--color-text-muted)]">
          Prophet 当前更适合作为趋势参考，而不是精确到价位的交易指令。这里把预测中枢、上下边界和最近收盘价并列展示，
          方便你快速判断未来 7 天的可能运行区间。
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <MetricCard label="预测中枢" value={money(props.targetPrice)} hint="未来预测末日 yhat" tone={tone} />
          <MetricCard label="下沿区间" value={money(props.lowerPrice)} hint="未来预测末日 yhat_lower" tone="gray" />
          <MetricCard label="上沿区间" value={money(props.upperPrice)} hint="未来预测末日 yhat_upper" tone="gray" />
        </div>
      </div>

      <div className="glass-panel rounded-[24px] p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-soft)]">风险提示</p>
        <h4 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">区间解释</h4>
        <div className="mt-4 space-y-3 text-sm leading-7 text-[var(--color-text-muted)]">
          <div className="glass-chip rounded-2xl px-4 py-3">
            最近收盘价：<span className="font-semibold text-[var(--color-text-strong)]">{money(props.lastClose)}</span>
          </div>
          <div className="glass-chip rounded-2xl px-4 py-3">
            预测涨跌幅：<span className={`font-semibold ${tone === "green" ? "text-[var(--color-profit)]" : tone === "yellow" ? "text-[var(--color-risk)]" : "text-[var(--color-text-strong)]"}`}>{percent(props.changePct)}</span>
          </div>
          <div className="glass-chip rounded-2xl px-4 py-3">
            如果预测中枢接近上沿，通常意味着模型趋势较强；如果中枢更靠近下沿，则意味着未来波动空间偏谨慎。
          </div>
          <div className="glass-chip rounded-2xl px-4 py-3">
            该结果更适合和市场分析、技术分析一起看，单独使用时请把它当作方向辅助，不要视作确定性结论。
          </div>
        </div>
      </div>
    </div>
  );
}

function ForecastTable(props: { rows: ForecastPoint[] }) {
  if (!props.rows.length) {
    return <EmptyStatePanel title="还没有未来预测明细" description="预测生成后，这里会展示未来 7 天的区间明细。" />;
  }

  return (
    <div className="glass-panel max-h-[560px] overflow-auto overscroll-contain rounded-[22px]">
      <table className="min-w-[760px] text-sm">
        <thead className="sticky top-0 z-10 bg-[rgba(255,255,255,0.8)] text-[var(--color-text-soft)] backdrop-blur-[14px]">
          <tr>
            {["日期", "预测中枢", "下沿区间", "上沿区间", "区间宽度"].map((label) => (
              <th key={label} className="whitespace-nowrap px-4 py-3 text-left font-medium">{label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(216,236,242,0.8)] text-[var(--color-text)]">
          {props.rows.map((item) => {
            const width =
              item.yhat_upper != null && item.yhat_lower != null && item.yhat
                ? ((item.yhat_upper - item.yhat_lower) / item.yhat) * 100
                : null;
            return (
              <tr key={item.ds}>
                <td className="whitespace-nowrap px-4 py-3">{item.ds.slice(0, 10)}</td>
                <td className="whitespace-nowrap px-4 py-3">{money(item.yhat)}</td>
                <td className="whitespace-nowrap px-4 py-3">{money(item.yhat_lower)}</td>
                <td className="whitespace-nowrap px-4 py-3">{money(item.yhat_upper)}</td>
                <td className="whitespace-nowrap px-4 py-3">{percent(width)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RiskAssessmentPanel(props: {
  changePct: number | null;
  uncertaintyPct: number | null;
  lastClose: number | null;
  targetPrice: number | null;
  lowerPrice: number | null;
  upperPrice: number | null;
}) {
  const directionRisk =
    props.changePct == null ? { level: "待观察", tone: "text-slate-200", desc: "当前还无法判断方向性风险。" } :
    props.changePct <= -3 ? { level: "偏高", tone: "text-[#FF9F43]", desc: "预测中枢明显低于最近收盘价，短期承压信号更强。" } :
    props.changePct < 1.5 ? { level: "中等", tone: "text-slate-200", desc: "预测中枢接近当前价格，方向判断并不极端，更多体现为震荡。" } :
    { level: "偏低", tone: "text-[#36D399]", desc: "预测中枢高于最近收盘价，方向上相对偏强。" };

  const intervalRisk =
    props.uncertaintyPct == null ? { level: "待观察", tone: "text-slate-200", desc: "当前还无法判断预测区间宽度。" } :
    props.uncertaintyPct >= 12 ? { level: "偏高", tone: "text-[#FF9F43]", desc: "上下边界距离较大，意味着模型不确定性更高。" } :
    props.uncertaintyPct >= 7 ? { level: "中等", tone: "text-slate-200", desc: "预测区间有一定宽度，建议结合技术面共同判断。" } :
    { level: "偏低", tone: "text-[#36D399]", desc: "预测区间较窄，短期波动空间相对可控。" };

  const deviationPct =
    props.lastClose != null && props.targetPrice != null && props.lastClose !== 0
      ? Math.abs((props.targetPrice - props.lastClose) / props.lastClose) * 100
      : null;
  const deviationRisk =
    deviationPct == null ? { level: "待观察", tone: "text-slate-200", desc: "当前无法判断预测中枢与现价的偏离程度。" } :
    deviationPct >= 8 ? { level: "偏高", tone: "text-[#FF9F43]", desc: "目标中枢与现价偏离较大，模型判断相对激进。" } :
    deviationPct >= 4 ? { level: "中等", tone: "text-slate-200", desc: "目标中枢与现价存在一定偏离，建议谨慎参考。" } :
    { level: "偏低", tone: "text-[#36D399]", desc: "目标中枢与现价接近，预测口径较稳。" };

  const overallScore = [directionRisk, intervalRisk, deviationRisk].reduce((sum, item) => {
    if (item.level === "偏高") return sum + 3;
    if (item.level === "中等") return sum + 2;
    if (item.level === "偏低") return sum + 1;
    return sum + 2;
  }, 0);
  const overall =
    overallScore >= 8 ? { label: "高风险", tone: "text-[#FF9F43]", desc: "建议把这组预测更多当作方向提醒，不要把中枢价格当成交易目标位。" } :
    overallScore >= 5 ? { label: "中风险", tone: "text-slate-200", desc: "可以参考趋势方向，但最好继续结合 MACD、RSI 和市场分析一起判断。" } :
    { label: "低风险", tone: "text-[#36D399]", desc: "当前预测区间和方向都相对平稳，但仍应视为辅助信息，而非确定性结论。" };

  const cards = [
    { title: "方向风险", value: directionRisk.level, tone: directionRisk.tone, desc: directionRisk.desc },
    { title: "区间风险", value: intervalRisk.level, tone: intervalRisk.tone, desc: intervalRisk.desc },
    { title: "偏离风险", value: deviationRisk.level, tone: deviationRisk.tone, desc: deviationRisk.desc },
  ];

  return (
    <div className="space-y-4 p-2">
      <div className="grid gap-3 xl:grid-cols-4">
        <MetricCard label="综合风险" value={overall.label} hint={overall.desc} tone={overall.label === "高风险" ? "yellow" : overall.label === "低风险" ? "green" : "gray"} />
        <MetricCard label="现价偏离" value={percent(deviationPct)} hint="预测中枢相对最近收盘价的绝对偏离" />
        <MetricCard label="下沿保护" value={money(props.lowerPrice)} hint="模型给出的未来区间下边界" />
        <MetricCard label="上沿空间" value={money(props.upperPrice)} hint="模型给出的未来区间上边界" />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {cards.map((item) => (
          <div key={item.title} className="glass-panel rounded-[24px] p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-soft)]">{item.title}</p>
            <h4 className={`mt-3 text-3xl font-semibold ${item.tone}`}>{item.value}</h4>
            <p className="mt-4 text-sm leading-7 text-[var(--color-text-muted)]">{item.desc}</p>
          </div>
        ))}
      </div>

      <div className="glass-panel rounded-[24px] p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-soft)]">风险结论</p>
        <h4 className={`mt-2 text-2xl font-semibold ${overall.tone}`}>{overall.label}</h4>
        <div className="mt-4 space-y-3 text-sm leading-7 text-[var(--color-text-muted)]">
          <p>{overall.desc}</p>
          <p>如果你看到“方向风险偏高”，通常说明预测中枢明显低于现价；如果“区间风险偏高”，说明上下边界较宽，不确定性更大。</p>
          <p>最稳妥的使用方式是把这里当作“未来 7 天的大致情景判断”，再和技术分析里的 MACD、RSI 以及市场分析页的数据交叉验证。</p>
        </div>
      </div>
    </div>
  );
}

export function ForecastPage({ ready, history, forecast }: ForecastPageProps) {
  if (!ready) {
    return <EmptyStatePanel title="请先在选股配置页选择股票后开始分析" description="趋势预测页会在同一个图表区域内切换预测主图、预测摘要、区间明细与后续扩展视图。" />;
  }

  const historyRows = history.filter((item) => item.close != null);
  const forecastRows = forecast.filter((item) => item.yhat != null && item.yhat_upper != null && item.yhat_lower != null);
  const futureRows = forecastRows.slice(-7);
  const lastHistory = historyRows[historyRows.length - 1];
  const lastForecast = futureRows[futureRows.length - 1];

  const lastClose = lastHistory?.close ?? null;
  const targetPrice = lastForecast?.yhat ?? null;
  const lowerPrice = lastForecast?.yhat_lower ?? null;
  const upperPrice = lastForecast?.yhat_upper ?? null;
  const changePct =
    lastClose != null && targetPrice != null && lastClose !== 0
      ? ((targetPrice - lastClose) / lastClose) * 100
      : null;
  const uncertaintyPct =
    targetPrice != null && lowerPrice != null && upperPrice != null && targetPrice !== 0
      ? ((upperPrice - lowerPrice) / targetPrice) * 100
      : null;

  const items =
    historyRows.length && forecastRows.length
      ? [
          {
            key: "forecast-main",
            label: "预测主图",
            summary: "把历史收盘、未来预测中枢和上下边界放在同一张图里，先看方向，再看区间。",
            content: <ForecastChart history={historyRows} forecast={forecastRows} />,
          },
          {
            key: "forecast-summary",
            label: "预测摘要",
            summary: "集中展示未来 7 天的预测方向、末日目标区间和区间解释，让趋势预测更容易读懂。",
            content: (
              <div className="space-y-4 p-2">
                <div className="grid gap-3 xl:grid-cols-4">
                  <MetricCard label="最近收盘价" value={money(lastClose)} hint="当前分析区间最后一个收盘点" />
                  <MetricCard
                    label="未来目标价"
                    value={money(targetPrice)}
                    hint="未来预测末日 yhat"
                    tone={changePct != null && changePct >= 0 ? "green" : "yellow"}
                  />
                  <MetricCard
                    label="预测涨跌幅"
                    value={percent(changePct)}
                    hint="相对最近收盘价估算"
                    tone={changePct != null && changePct >= 0 ? "green" : "yellow"}
                  />
                  <MetricCard label="区间不确定性" value={percent(uncertaintyPct)} hint="(上沿 - 下沿) / 预测中枢" />
                </div>
                <ScenarioPanel
                  targetPrice={targetPrice}
                  lowerPrice={lowerPrice}
                  upperPrice={upperPrice}
                  lastClose={lastClose}
                  changePct={changePct}
                />
              </div>
            ),
          },
          {
            key: "forecast-table",
            label: "预测明细",
            summary: "逐日查看未来 7 天的预测中枢和上下边界，便于和交易计划或观察日历对照。",
            content: (
              <div className="space-y-4 p-2">
                <div className="grid gap-3 md:grid-cols-3">
                  <MetricCard label="预测天数" value={`${futureRows.length} 天`} hint="当前默认使用 7 天预测窗口" />
                  <MetricCard label="最高预测上沿" value={money(Math.max(...futureRows.map((item) => item.yhat_upper as number)))} hint="未来区间上边界的最大值" />
                  <MetricCard label="最低预测下沿" value={money(Math.min(...futureRows.map((item) => item.yhat_lower as number)))} hint="未来区间下边界的最小值" />
                </div>
                <ForecastTable rows={futureRows} />
              </div>
            ),
          },
          {
            key: "risk-assessment",
            label: "风险评估",
            summary: "根据预测方向、区间宽度和现价偏离程度，给出当前预测结果的风险解释。",
            content: (
              <RiskAssessmentPanel
                changePct={changePct}
                uncertaintyPct={uncertaintyPct}
                lastClose={lastClose}
                targetPrice={targetPrice}
                lowerPrice={lowerPrice}
                upperPrice={upperPrice}
              />
            ),
          },
        ]
      : [];

  return <ChartCarousel title="趋势预测" eyebrow="主内容区" items={items} emptyTitle="当前还没有趋势预测数据" emptyDescription="请先在配置页完成股票选择并加载分析数据。" />;
}
