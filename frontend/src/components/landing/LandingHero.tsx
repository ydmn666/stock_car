import { AppButton } from "../common/AppButton";
import { RevealSection } from "../common/RevealSection";

type LandingHeroProps = {
  health: string;
  onLogin: () => void;
  onExplore: () => void;
};

export function LandingHero({ health, onLogin, onExplore }: LandingHeroProps) {
  return (
    <section className="glass-panel-soft overflow-hidden rounded-[34px] px-7 py-10 lg:px-10 lg:py-12">
      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
        <RevealSection className="space-y-8" delayMs={60}>
          <div className="inline-flex rounded-full border border-[rgba(53,208,181,0.22)] bg-[rgba(53,208,181,0.08)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-[var(--color-accent)]">
            新能源 A 股智能分析平台
          </div>
          <div className="max-w-4xl">
            <h1 className="text-5xl font-black leading-[1.02] text-[var(--color-text-strong)] md:text-7xl">
              用<span className="text-[var(--color-primary)]"> AI </span>掌握
              <br />
              <span className="text-[var(--color-accent)]">新能源</span>股票与个人投资全局
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-9 text-[var(--color-text-muted)]">
              聚合 A 股主流数据，统一处理行情、资讯、情绪与趋势预测，
              同时记录真实持仓、成本投入和收益变化，让分析结果真正落到个人决策上。
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <AppButton onClick={onLogin}>进入指挥台</AppButton>
            <AppButton variant="secondary" onClick={onExplore}>预览核心页面</AppButton>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["覆盖市场", "A 股", "统一股票与新闻模型"],
              ["核心能力", "行情 + AI + 投资", "分析与个人资产同屏协同"],
              ["输出形态", "图表 / 报告 / 问答", "支持 PDF 导出与智能解释"],
            ].map(([label, value, hint], index) => (
              <RevealSection key={label} delayMs={160 + index * 70}>
                <div className="data-card rounded-[24px] px-5 py-4">
                  <p className="text-sm text-[var(--color-text-soft)]">{label}</p>
                  <p className="mt-3 text-[2rem] font-semibold tracking-[-0.02em] text-[var(--color-text-strong)]">{value}</p>
                  <p className={`mt-2 text-sm ${index !== 1 ? "text-[var(--color-text-soft)]" : "text-[var(--color-text-muted)]"}`}>{hint}</p>
                </div>
              </RevealSection>
            ))}
          </div>
        </RevealSection>

        <RevealSection delayMs={180}>
          <aside className="glass-panel rounded-[28px] p-5">
            <div className="flex items-center justify-between text-sm">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-soft)]">实时观察</p>
                <h3 className="mt-2 text-xl font-semibold text-[var(--color-text-strong)]">新能源热点行情</h3>
              </div>
              <span className="rounded-full border border-[rgba(53,208,181,0.18)] bg-[rgba(53,208,181,0.08)] px-3 py-1 text-xs text-[var(--color-accent)]">{health === "ok" ? "系统在线" : "状态检测中"}</span>
            </div>
            <div className="mt-5 space-y-3">
              {[
                ["比亚迪", "002594.SZ", "￥234.10", "+3.85%"],
                ["宁德时代", "300750.SZ", "￥265.40", "+2.11%"],
                ["长安汽车", "000625.SZ", "￥16.82", "-0.45%"],
              ].map(([name, code, price, change]) => (
                <div key={code} className="data-card flex items-center justify-between rounded-2xl px-4 py-4 transition hover:border-[color:var(--color-primary-border)]">
                  <div>
                    <p className="font-semibold text-[var(--color-text-strong)]">{name}</p>
                    <p className="mt-1 text-xs text-[var(--color-text-soft)]">{code}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-[var(--color-text-strong)]">{price}</p>
                    <p className={`mt-1 text-sm ${change.startsWith("-") ? "text-[var(--color-risk)]" : "text-[var(--color-profit)]"}`}>{change}</p>
                  </div>
                </div>
              ))}
            </div>
          </aside>
        </RevealSection>
      </div>
    </section>
  );
}

