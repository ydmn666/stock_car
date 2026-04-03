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
          item.tone === "green" ? "text-[var(--color-profit)]" : item.tone === "yellow" ? "text-[var(--color-risk)]" : "text-[var(--color-text-soft)]";
        return (
          <div key={item.label} className="glass-panel rounded-[24px] px-5 py-4">
            <p className="text-sm text-[var(--color-text-soft)]">{item.label}</p>
            <p className="mt-3 text-3xl font-semibold text-[var(--color-text-strong)]">{item.value}</p>
            {item.hint ? <p className={`mt-2 text-sm ${toneClass}`}>{item.hint}</p> : null}
          </div>
        );
      })}
    </div>
  );
}
