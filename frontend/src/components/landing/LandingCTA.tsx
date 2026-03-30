import { AppButton } from "../common/AppButton";
import { RevealSection } from "../common/RevealSection";

type LandingCTAProps = {
  onLogin: () => void;
};

export function LandingCTA({ onLogin }: LandingCTAProps) {
  return (
    <RevealSection delayMs={80}>
      <section className="rounded-[30px] border border-white/8 bg-[linear-gradient(180deg,#111827_0%,#0f172a_100%)] px-8 py-12 text-center shadow-[0_24px_80px_rgba(2,6,23,0.28)]">
        <p className="text-xs uppercase tracking-[0.24em] text-slate-500">准备开始</p>
        <h3 className="mt-3 text-4xl font-black text-white md:text-5xl">开始你的新能源汽车智能投研流程</h3>
        <p className="mx-auto mt-4 max-w-3xl text-base leading-8 text-slate-300">
          登录后进入核心工作台，后续将支持独立选股配置、技术分析轮播、舆情判断、趋势预测与个人投资模块联动。
        </p>
        <div className="mt-8 flex justify-center">
          <AppButton onClick={onLogin} className="px-8 py-4 text-base">立即进入登录页</AppButton>
        </div>
      </section>
    </RevealSection>
  );
}
