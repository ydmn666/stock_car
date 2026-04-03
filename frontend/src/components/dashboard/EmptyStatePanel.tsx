type EmptyStatePanelProps = {
  title: string;
  description: string;
};

export function EmptyStatePanel({ title, description }: EmptyStatePanelProps) {
  return (
    <div className="glass-panel flex min-h-[280px] items-center justify-center rounded-[28px] border-dashed px-8 py-10 text-center">
      <div className="max-w-xl">
        <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-soft)]">等待分析上下文</p>
        <h3 className="mt-4 text-3xl font-semibold text-[var(--color-text-strong)]">{title}</h3>
        <p className="mt-4 text-sm leading-7 text-[var(--color-text-muted)]">{description}</p>
      </div>
    </div>
  );
}
