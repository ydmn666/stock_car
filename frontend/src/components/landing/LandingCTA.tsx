import { AppButton } from "../common/AppButton";
import { RevealSection } from "../common/RevealSection";

type LandingCTAProps = {
  onLogin: () => void;
};

export function LandingCTA({ onLogin }: LandingCTAProps) {
  return (
    <RevealSection delayMs={80}>
      <section className="glass-panel-soft rounded-[30px] px-8 py-12 text-center">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--color-text-soft)]">准备开始</p>
        <h3 className="mt-3 text-4xl font-black text-[var(--color-text-strong)] md:text-5xl">开始你的新能源汽车智能投研流程</h3>
        <p className="mx-auto mt-4 max-w-3xl text-base leading-8 text-[var(--color-text-muted)]">
          登录后进入核心工作台，后续将支持独立选股配置、技术分析轮播、舆情判断、趋势预测与个人投资模块联动。
        </p>
        <div className="mt-8 flex justify-center">
          <AppButton onClick={onLogin} className="px-8 py-4 text-base">立即进入登录页</AppButton>
        </div>
      </section>
    </RevealSection>
  );
}
