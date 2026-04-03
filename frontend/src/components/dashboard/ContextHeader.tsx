import type { ReactNode } from "react";
import type { Instrument } from "../../types";

type ContextHeaderProps = {
  activeStock: Instrument | null;
  startDate: string;
  endDate: string;
  actions?: ReactNode;
};

export function ContextHeader({ activeStock, startDate, endDate, actions }: ContextHeaderProps) {
  return (
    <section className="glass-panel-soft rounded-[30px] p-6">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-soft)]">核心工作台</p>
          <h1 className="mt-3 text-4xl font-black text-[var(--color-text-strong)] xl:text-5xl">{activeStock ? `${activeStock.display_name} · ${activeStock.full_symbol}` : "请先完成选股配置"}</h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--color-text-muted)] xl:text-base xl:leading-8">
            当前工作区聚焦新能源汽车赛道股票分析。中间区域只显示当前模块，右侧智能问答会结合所选股票与时间区间解释页面内容。
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-[var(--color-text-muted)]">
            <span className="glass-chip rounded-full px-3 py-2">分析起点 {startDate}</span>
            <span className="glass-chip rounded-full px-3 py-2">分析终点 {endDate}</span>
            {activeStock ? <span className="glass-chip rounded-full px-3 py-2">市场 A股</span> : null}
          </div>
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </section>
  );
}

