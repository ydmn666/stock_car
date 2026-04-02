import { NewsHeatChart, SentimentGaugeChart } from "../../components/charts";
import { ChartCarousel } from "../../components/dashboard/ChartCarousel";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import { getNewsTime, getNewsTitle, getNewsUrl } from "../../lib/workspace";
import type { NewsItem } from "../../types";

type SentimentPageProps = {
  ready: boolean;
  activeNews: NewsItem[];
  activeNewsFallback: boolean;
};

function NewsList({ items, fallback }: { items: NewsItem[]; fallback: boolean }) {
  return (
    <div className="space-y-3 rounded-[24px] border border-white/8 bg-[#101010] p-4">
      <div className="rounded-2xl border border-white/8 bg-white/4 px-4 py-3 text-sm text-slate-300">{fallback ? "当前展示的是行业回退资讯，用于避免个股新闻缺失。" : "当前展示的是与所选股票直接相关的最新资讯。"}</div>
      <div className="max-h-[460px] space-y-3 overflow-y-auto overscroll-contain pr-1">
        {items.slice(0, 10).map((item) => {
          const url = getNewsUrl(item);
          return (
            <div key={item.id} className="rounded-2xl border border-white/8 bg-[#0d0d0d] px-4 py-4">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">{getNewsTime(item)}</div>
              <div className="mt-2 text-sm leading-7 text-zinc-200">{getNewsTitle(item)}</div>
              {url ? <a href={url} target="_blank" rel="noreferrer" className="mt-3 inline-flex text-sm text-[#165DFF] hover:underline">查看原文</a> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function SentimentPage({ ready, activeNews, activeNewsFallback }: SentimentPageProps) {
  if (!ready) {
    return <EmptyStatePanel title="请先在选股配置页选择股票后开始分析" description="资讯舆情页会在同一个区域内切换新闻列表、新闻热度与情绪评分，而不是把信息纵向堆成很长的页面。" />;
  }

  const items = activeNews.length
    ? [
        {
          key: "news-list",
          label: "新闻列表",
          summary: "集中查看当前主标的的新闻流与原文链接，列表本身采用局部滚动。",
          content: <NewsList items={activeNews} fallback={activeNewsFallback} />,
        },
        {
          key: "sentiment-score",
          label: "情绪评分",
          summary: "用轻量情绪评分面板概括当前舆情偏向。",
          content: <SentimentGaugeChart score={activeNewsFallback ? 56 : 78} />,
        },
        {
          key: "news-heat",
          label: "新闻热度",
          summary: "按日期聚合新闻热度，帮助识别近期舆情集中爆发时段。",
          content: <NewsHeatChart records={activeNews} />,
        },
      ]
    : [];

  return <ChartCarousel title="资讯舆情" eyebrow="主内容区" items={items} emptyTitle="当前还没有资讯舆情数据" emptyDescription="请先在配置页完成股票选择并加载分析数据。" />;
}
