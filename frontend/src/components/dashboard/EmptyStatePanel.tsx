type EmptyStatePanelProps = {
  title: string;
  description: string;
};

export function EmptyStatePanel({ title, description }: EmptyStatePanelProps) {
  return (
    <div className="flex min-h-[280px] items-center justify-center rounded-[28px] border border-dashed border-white/10 bg-[#121212] px-8 py-10 text-center">
      <div className="max-w-xl">
        <p className="text-xs uppercase tracking-[0.22em] text-slate-500">等待分析上下文</p>
        <h3 className="mt-4 text-3xl font-semibold text-white">{title}</h3>
        <p className="mt-4 text-sm leading-7 text-slate-300">{description}</p>
      </div>
    </div>
  );
}
