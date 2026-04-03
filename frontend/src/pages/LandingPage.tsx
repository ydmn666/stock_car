import { LandingCTA } from "../components/landing/LandingCTA";
import { LandingFeatureGrid } from "../components/landing/LandingFeatureGrid";
import { LandingHero } from "../components/landing/LandingHero";

type LandingPageProps = {
  health: string;
  onLogin: () => void;
  onExplore: () => void;
};

export function LandingPage({ health, onLogin, onExplore }: LandingPageProps) {
  return (
    <div className="app-aurora min-h-screen text-[var(--color-text)]">
      <div className="app-aurora__wave app-aurora__wave--left" />
      <div className="app-aurora__wave app-aurora__wave--right" />
      <div className="app-aurora__grid" />
      <header className="sticky top-0 z-20 border-b border-[var(--color-border)] bg-[rgba(255,255,255,0.62)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1680px] items-center justify-between gap-6 px-6 py-5">
          <div className="flex items-center gap-10">
            <span className="text-2xl font-black tracking-tight text-[var(--color-primary)]">动能智投</span>
            <nav className="hidden items-center gap-8 text-sm text-[var(--color-text-muted)] md:flex">
              <span className="text-[var(--color-accent)]">市场全景</span>
              <span>AI 洞察</span>
              <span>投资组合</span>
              <span>资讯舆情</span>
            </nav>
          </div>
          <div className="text-xs uppercase tracking-[0.16em] text-[var(--color-text-soft)]">新能源汽车智能投研平台</div>
        </div>
      </header>

      <main className="relative mx-auto max-w-[1680px] space-y-6 px-6 py-8 pb-12">
        <LandingHero health={health} onLogin={onLogin} onExplore={onExplore} />
        <LandingFeatureGrid />
        <LandingCTA onLogin={onLogin} />
      </main>
    </div>
  );
}
