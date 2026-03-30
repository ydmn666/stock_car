import { ForecastChart } from "../../components/charts";
import { ChartCarousel } from "../../components/dashboard/ChartCarousel";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import type { StockRecord } from "../../types";

type ForecastPageProps = {
  ready: boolean;
  history: StockRecord[];
  forecast: StockRecord[];
};

function PlaceholderPanel({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex h-[420px] items-center justify-center rounded-[24px] border border-dashed border-white/10 bg-[#101010] p-6 text-center">
      <div className="max-w-xl">
        <h4 className="text-2xl font-semibold text-white">{title}</h4>
        <p className="mt-4 text-sm leading-7 text-slate-300">{description}</p>
      </div>
    </div>
  );
}

export function ForecastPage({ ready, history, forecast }: ForecastPageProps) {
  if (!ready) {
    return <EmptyStatePanel title="请先在选股配置页选择股票后开始分析" description="趋势预测页会在同一个图表区域内切换预测主图、风险区间说明和后续扩展视图。" />;
  }

  const items =
    history.length && forecast.length
      ? [
          {
            key: "forecast-main",
            label: "预测主图",
            summary: "展示历史收盘与未来区间预测，是趋势预测模块的核心视图。",
            content: <ForecastChart history={history} forecast={forecast} />,
          },
          {
            key: "risk-band",
            label: "风险区间",
            summary: "预留风险区间解释位，后续可接更细的置信区间和风险分层模型。",
            content: <PlaceholderPanel title="风险区间说明" description="后续这里会加入预测区间解释、上行/下行概率摘要与风险分层提示。" />,
          },
        ]
      : [];

  return <ChartCarousel title="趋势预测" eyebrow="主内容区" items={items} emptyTitle="当前还没有趋势预测数据" emptyDescription="请先在配置页完成股票选择并加载分析数据。" />;
}
