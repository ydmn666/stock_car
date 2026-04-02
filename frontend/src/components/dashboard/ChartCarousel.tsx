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
    <section className="rounded-[28px] border border-white/8 bg-[#111827] p-5 shadow-[0_24px_80px_rgba(2,6,23,0.28)]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{eyebrow}</p>
          <h3 className="mt-2 text-2xl font-semibold text-white">{title}</h3>
          <p className="mt-2 text-sm leading-7 text-slate-300">{active.summary}</p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => move(-1)} className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/4 text-slate-300 transition hover:bg-white/8">←</button>
          <button type="button" onClick={() => move(1)} className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/4 text-slate-300 transition hover:bg-white/8">→</button>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {items.map((item, index) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setActiveIndex(index)}
            className={`rounded-2xl px-4 py-2 text-sm font-medium transition ${index === activeIndex ? "bg-[#165DFF] text-white" : "bg-white/4 text-slate-300 hover:bg-white/8"}`}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="mt-4 overflow-hidden rounded-[24px] bg-[#0f172a] p-2">{active.content}</div>
    </section>
  );
}
