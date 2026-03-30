import { KLineChart, ReturnChart } from "../../components/charts";
import { ChartCarousel } from "../../components/dashboard/ChartCarousel";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import type { StockRecord } from "../../types";

type TechnicalAnalysisPageProps = {
  ready: boolean;
  activeRecords: StockRecord[];
};

function PlaceholderChart({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex h-[520px] items-center justify-center rounded-[24px] border border-dashed border-white/10 bg-[#101010] p-6 text-center">
      <div className="max-w-xl">
        <h4 className="text-2xl font-semibold text-white">{title}</h4>
        <p className="mt-4 text-sm leading-7 text-slate-300">{description}</p>
      </div>
    </div>
  );
}

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
          summary: "这里先预留 MACD 视图位，后续接真实指标计算即可直接替换。",
          content: <PlaceholderChart title="MACD 指标区域" description="后续接入真实技术指标后，这里将显示 MACD 柱体、DIF 与 DEA 曲线。" />,
        },
        {
          key: "rsi",
          label: "RSI",
          summary: "这里先预留 RSI 视图位，用于后续接入技术指标计算结果。",
          content: <PlaceholderChart title="RSI 指标区域" description="后续会在这里展示 RSI 超买超卖区间，用于辅助判断短期热度。" />,
        },
      ]
    : [];

  return <ChartCarousel title="技术分析" eyebrow="主内容区" items={items} emptyTitle="当前还没有技术分析数据" emptyDescription="请先在配置页完成股票选择并加载分析数据。" />;
}
