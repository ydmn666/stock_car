import { useState } from "react";
import { EmptyStatePanel } from "./EmptyStatePanel";

type ChartCarouselItem = {
  key: string;
  label: string;
  summary: string;
  content: React.ReactNode;
};

type ChartCarouselProps = {
  title: string;
  eyebrow: string;
  items: ChartCarouselItem[];
  emptyTitle: string;
  emptyDescription: string;
};

export function ChartCarousel({ title, eyebrow, items, emptyTitle, emptyDescription }: ChartCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  if (!items.length) {
    return <EmptyStatePanel title={emptyTitle} description={emptyDescription} />;
  }

  const active = items[activeIndex] ?? items[0];

  function move(offset: number) {
    setActiveIndex((current) => {
      const next = current + offset;
      if (next < 0) return items.length - 1;
      if (next >= items.length) return 0;
      return next;
    });
  }

  return (
    <section className="glass-panel rounded-[28px] p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-soft)]">{eyebrow}</p>
          <h3 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">{title}</h3>
          <p className="mt-2 text-sm leading-7 text-[var(--color-text-muted)]">{active.summary}</p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => move(-1)} className="glass-chip flex h-10 w-10 items-center justify-center rounded-2xl text-[var(--color-text-muted)] transition hover:bg-white/85">←</button>
          <button type="button" onClick={() => move(1)} className="glass-chip flex h-10 w-10 items-center justify-center rounded-2xl text-[var(--color-text-muted)] transition hover:bg-white/85">→</button>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {items.map((item, index) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setActiveIndex(index)}
            className={`rounded-2xl px-4 py-2 text-sm font-medium transition ${index === activeIndex ? "selected-chip" : "glass-chip text-[var(--color-text-muted)] hover:bg-white/85"}`}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="content-card mt-4 overflow-hidden rounded-[24px] p-2">{active.content}</div>
    </section>
  );
}
