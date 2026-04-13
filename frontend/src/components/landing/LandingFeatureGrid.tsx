import { RevealSection } from "../common/RevealSection";

export function LandingFeatureGrid() {
  return (
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.7fr)]">
      <RevealSection delayMs={60}>
        <div className="glass-panel rounded-[28px] p-5">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--color-text-soft)]">产品定位</p>
          <h3 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">平台核心价值</h3>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <div className="content-card rounded-[24px] p-5 transition hover:border-[color:var(--color-primary-border)]">
              <p className="text-lg font-semibold text-[var(--color-text-strong)]">多市场统一分析</p>
              <p className="mt-3 text-sm leading-7 text-[var(--color-text-muted)]">将分散的股票来源做统一标准化处理，让前端专注展示，避免受单一数据接口波动影响。</p>
            </div>
            <div className="content-card rounded-[24px] p-5 transition hover:border-[color:var(--color-primary-border)]">
              <p className="text-lg font-semibold text-[var(--color-text-strong)]">通用 AI 智能助手</p>
              <p className="mt-3 text-sm leading-7 text-[var(--color-text-muted)]">不再拆成多个专用问答面板，而是通过一个右侧 AI 助手统一解释市场、资讯、报告与持仓变化。</p>
            </div>
            <div className="data-card rounded-[24px] p-5 text-[var(--color-text-strong)]">
              <p className="text-lg font-semibold">个人投资闭环</p>
              <p className="mt-3 text-sm leading-7 text-[var(--color-text-muted)]">从数据分析延伸到真实投资记录、成本投入、收益波动与资金管理，形成完整决策工作台。</p>
            </div>
          </div>
        </div>
      </RevealSection>

      <RevealSection delayMs={140}>
        <div className="glass-panel rounded-[28px] p-5">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--color-text-soft)]">交互结构</p>
          <h3 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">进入工作台后的使用方式</h3>
          <div className="mt-5 space-y-4 text-sm leading-7 text-[var(--color-text-muted)]">
            <p>参考 VS Code 的高密度布局，左侧负责导航和流程推进，中间主区域聚焦图表与数据，右侧只保留紧凑的智能问答面板。</p>
            <p>这样既能保持内容清晰，也为后续个人投资模块、多市场数据接入和图表轮播留出足够空间。</p>
          </div>
        </div>
      </RevealSection>
    </section>
  );
}
