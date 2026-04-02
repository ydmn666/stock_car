import { AppButton } from "../common/AppButton";
import { RevealSection } from "../common/RevealSection";

type LandingHeroProps = {
  health: string;
  onLogin: () => void;
  onExplore: () => void;
};

export function LandingHero({ health, onLogin, onExplore }: LandingHeroProps) {
  return (
    <section className="overflow-hidden rounded-[34px] border border-white/8 bg-[radial-gradient(circle_at_top_left,rgba(22,93,255,0.18),transparent_28%),linear-gradient(180deg,#111827_0%,#0f172a_100%)] px-7 py-10 lg:px-10 lg:py-12">
      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
        <RevealSection className="space-y-8" delayMs={60}>
          <div className="inline-flex rounded-full border border-[#36D399]/25 bg-[#36D399]/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-[#36D399]">
            新能源 A 股智能分析平台
          </div>
          <div className="max-w-4xl">
            <h1 className="text-5xl font-black leading-[1.02] text-white md:text-7xl">
              用<span className="text-[#165DFF]"> AI </span>掌握
              <br />
              新能源股票与个人投资全局
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-9 text-slate-300">
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
                <div className="rounded-[24px] border border-white/8 bg-[#0f172a] px-5 py-4">
                  <p className="text-sm text-slate-500">{label}</p>
                  <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
                  <p className={`mt-2 text-sm ${index !== 1 ? "text-[#36D399]" : "text-slate-300"}`}>{hint}</p>
                </div>
              </RevealSection>
            ))}
          </div>
        </RevealSection>

        <RevealSection delayMs={180}>
          <aside className="rounded-[28px] border border-white/8 bg-[#0f172a]/90 p-5">
            <div className="flex items-center justify-between text-sm">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">实时观察</p>
                <h3 className="mt-2 text-xl font-semibold text-white">新能源热点行情</h3>
              </div>
              <span className="rounded-full bg-[#36D399]/10 px-3 py-1 text-xs text-[#36D399]">{health === "ok" ? "系统在线" : "状态检测中"}</span>
            </div>
            <div className="mt-5 space-y-3">
              {[
                ["比亚迪", "002594.SZ", "￥234.10", "+3.85%"],
                ["宁德时代", "300750.SZ", "￥265.40", "+2.11%"],
                ["长安汽车", "000625.SZ", "￥16.82", "-0.45%"],
              ].map(([name, code, price, change]) => (
                <div key={code} className="flex items-center justify-between rounded-2xl border border-white/8 bg-[#111827] px-4 py-4 transition hover:-translate-y-0.5 hover:border-[#165DFF]/20">
                  <div>
                    <p className="font-semibold text-white">{name}</p>
                    <p className="mt-1 text-xs text-slate-500">{code}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-white">{price}</p>
                    <p className={`mt-1 text-sm ${change.startsWith("-") ? "text-[#F87272]" : "text-[#FF9F43]"}`}>{change}</p>
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

