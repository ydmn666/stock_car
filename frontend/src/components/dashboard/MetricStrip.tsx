type MetricStripProps = {
  items: Array<{
    label: string;
    value: string;
    hint?: string;
    tone?: "green" | "yellow" | "gray";
  }>;
};

export function MetricStrip({ items }: MetricStripProps) {
  return (
    <div className="grid gap-3 xl:grid-cols-4">
      {items.map((item) => {
        const toneClass =
          item.tone === "green" ? "text-[#36D399]" : item.tone === "yellow" ? "text-[#FF9F43]" : "text-slate-500";
        return (
          <div key={item.label} className="rounded-[24px] border border-white/8 bg-[#111827] px-5 py-4">
            <p className="text-sm text-slate-500">{item.label}</p>
            <p className="mt-3 text-3xl font-semibold text-white">{item.value}</p>
            {item.hint ? <p className={`mt-2 text-sm ${toneClass}`}>{item.hint}</p> : null}
          </div>
        );
      })}
    </div>
  );
}
