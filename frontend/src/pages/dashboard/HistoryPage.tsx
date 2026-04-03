import { AppButton } from "../../components/common/AppButton";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import type { HistoryItem } from "../../types";

type HistoryPageProps = {
  items: HistoryItem[];
  onSetActiveCode: (code: string) => void;
  onDelete: (id: number) => void;
};

export function HistoryPage({ items, onSetActiveCode, onDelete }: HistoryPageProps) {
  if (!items.length) {
    return <EmptyStatePanel title="当前用户还没有访问历史" description="当你在工作台中查看分析结果后，访问记录会出现在这里。" />;
  }

  return (
    <section className="glass-panel rounded-[28px] p-5">
      <div className="mb-5">
        <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-soft)]">历史记录</p>
        <h3 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">最近访问与分析轨迹</h3>
      </div>
      <div className="max-h-[620px] space-y-3 overflow-y-auto overscroll-contain pr-1">
        {items.map((item) => (
          <div key={item.id} className="glass-panel flex flex-wrap items-center justify-between gap-3 rounded-2xl px-4 py-4">
            <div>
              <div className="font-medium text-[var(--color-text-strong)]">{item.stock_name} ({item.stock_code})</div>
              <div className="mt-1 text-sm text-[var(--color-text-soft)]">{item.visit_time_str}</div>
            </div>
            <div className="flex gap-2">
              <AppButton variant="secondary" onClick={() => onSetActiveCode(item.stock_code)}>设为当前股票</AppButton>
              <AppButton variant="ghost" onClick={() => onDelete(item.id)}>删除</AppButton>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
