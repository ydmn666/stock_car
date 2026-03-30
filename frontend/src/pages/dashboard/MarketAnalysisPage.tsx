import { ComparisonChart, ReturnChart } from "../../components/charts";
import { ChartCarousel } from "../../components/dashboard/ChartCarousel";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import { DataTable } from "../../components/dashboard/DataTable";
import type { StockRecord } from "../../types";

type MarketAnalysisPageProps = {
  ready: boolean;
  activeRecords: StockRecord[];
  comparisonSeries: Array<{ name: string; records: StockRecord[] }>;
};

export function MarketAnalysisPage({ ready, activeRecords, comparisonSeries }: MarketAnalysisPageProps) {
  if (!ready) {
    return <EmptyStatePanel title="请先在选股配置页选择股票后开始分析" description="完成配置后，这里会展示区间收益曲线、跨股票对比以及最近行情明细。" />;
  }

  const items = [];
  if (activeRecords.length) {
    items.push({
      key: "returns",
      label: "收益曲线",
      summary: "用单一舞台区域聚焦当前主标的的区间收益变化，不再向下堆叠多张图。",
      content: <ReturnChart records={activeRecords} />,
    });
  }
  if (comparisonSeries.filter((item) => item.records.length > 1).length >= 2) {
    items.push({
      key: "comparison",
      label: "对比图",
      summary: "横向比较多只股票在同一分析区间内的表现差异。",
      content: <ComparisonChart series={comparisonSeries} />,
    });
  }
  if (activeRecords.length) {
    items.push({
      key: "table",
      label: "行情明细",
      summary: "保留最近行情明细表，通过局部滚动承载数据，不再拉长整个页面。",
      content: <DataTable records={activeRecords} />,
    });
  }

  return <ChartCarousel title="市场分析" eyebrow="主内容区" items={items} emptyTitle="当前还没有市场分析数据" emptyDescription="请先在配置页完成股票选择并加载分析数据。" />;
}
