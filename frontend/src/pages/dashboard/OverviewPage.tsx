import { ComparisonChart } from "../../components/charts";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import { getNewsTime, getNewsTitle, money, percent, pricePrefix } from "../../lib/workspace";
import type { Instrument, NewsItem, PriceBar } from "../../types";

type OverviewPageProps = {
  ready: boolean;
  activeStock: Instrument | null;
  comparisonSeries: Array<{ name: string; records: PriceBar[] }>;
  activeNews: NewsItem[];
  latestRecord?: PriceBar;
};

function StatCard(props: { label: string; value: string; hint?: string }) {
  return (
    <div className="data-card rounded-[24px] px-5 py-4">
      <p className="text-sm text-[var(--color-text-soft)]">{props.label}</p>
      <p className="mt-3 text-[2rem] font-semibold tracking-[-0.02em] text-[var(--color-text-strong)]">{props.value}</p>
      {props.hint ? <p className="mt-2 text-sm text-[var(--color-text-muted)]">{props.hint}</p> : null}
    </div>
  );
}

export function OverviewPage({ ready, activeStock, comparisonSeries, activeNews, latestRecord }: OverviewPageProps) {
  if (!ready) {
    return <EmptyStatePanel title="请先在选股配置页选择股票后开始分析" description="完成市场、股票与时间区间配置后，这里会展示多股收益对比、当前行情摘要和最近资讯摘要。" />;
  }

  const validSeries = comparisonSeries.filter((item) => item.records.length > 1);
  const prefix = pricePrefix(activeStock);

  return (
    <div className="space-y-4">
      <section className="glass-panel rounded-[28px] p-5">
        <div className="mb-5">
          <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-soft)]">总览</p>
          <h3 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">多股票收益对比</h3>
        </div>
        {validSeries.length >= 2 ? (
          <div className="glass-panel overflow-hidden rounded-[24px] p-2"><ComparisonChart series={comparisonSeries} /></div>
        ) : (
          <EmptyStatePanel title="至少需要两只有效股票" description="当前已选股票里，至少两只成功加载区间行情后，这里才会显示收益率对比图。" />
        )}
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="glass-panel rounded-[28px] p-5">
          <div className="mb-5">
            <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-soft)]">总览</p>
            <h3 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">当前行情摘要</h3>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <StatCard label="开盘价" value={money(latestRecord?.open ?? null, prefix)} />
            <StatCard label="最高价" value={money(latestRecord?.high ?? null, prefix)} />
            <StatCard label="最低价" value={money(latestRecord?.low ?? null, prefix)} />
            <StatCard label="涨跌幅" value={percent(latestRecord?.pct_change ?? null)} hint="以当前主标的最新数据计算" />
          </div>
        </div>

        <div className="glass-panel rounded-[28px] p-5">
          <div className="mb-5">
            <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-soft)]">总览</p>
            <h3 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">最近资讯</h3>
          </div>
          <div className="space-y-3">
            {activeNews.slice(0, 4).map((item) => (
              <div key={item.id} className="content-card rounded-2xl px-4 py-4">
                <div className="text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">{getNewsTime(item)}</div>
                <div className="mt-2 text-sm leading-7 text-[var(--color-text)]">{getNewsTitle(item)}</div>
              </div>
            ))}
            {!activeNews.length ? <p className="text-sm text-[var(--color-text-soft)]">当前暂无资讯摘要。</p> : null}
          </div>
        </div>
      </section>
    </div>
  );
}
