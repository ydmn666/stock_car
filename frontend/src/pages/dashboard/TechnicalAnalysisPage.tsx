import { KLineChart, MacdChart, ReturnChart, RsiChart } from "../../components/charts";
import { ChartCarousel } from "../../components/dashboard/ChartCarousel";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import type { PriceBar } from "../../types";

type TechnicalAnalysisPageProps = {
  ready: boolean;
  activeRecords: PriceBar[];
};

export function TechnicalAnalysisPage({ ready, activeRecords }: TechnicalAnalysisPageProps) {
  if (!ready) {
    return <EmptyStatePanel title="请先在选股配置页选择股票后开始分析" description="技术分析页会在同一个图表舞台里，通过标签与左右箭头切换 K 线、收益曲线、MACD、RSI 等视图。" />;
  }

  const items = activeRecords.length
    ? [
        {
          key: "kline",
          label: "K 线",
          summary: "当前主标的的价格走势与均线表现，作为技术分析的中心视觉。",
          content: <KLineChart records={activeRecords} />,
        },
        {
          key: "return",
          label: "收益",
          summary: "辅助观察区间收益曲线，快速定位阶段性趋势变化。",
          content: <ReturnChart records={activeRecords} />,
        },
        {
          key: "macd",
          label: "MACD",
          summary: "通过 DIF、DEA 和红绿柱观察趋势强弱变化与潜在拐点。",
          content: <MacdChart records={activeRecords} />,
        },
        {
          key: "rsi",
          label: "RSI",
          summary: "观察超买超卖区间，辅助判断短期热度和回落风险。",
          content: <RsiChart records={activeRecords} />,
        },
      ]
    : [];

  return <ChartCarousel title="技术分析" eyebrow="主内容区" items={items} emptyTitle="当前还没有技术分析数据" emptyDescription="请先在配置页完成股票选择并加载分析数据。" />;
}
