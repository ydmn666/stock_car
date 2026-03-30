import type { FormEvent } from "react";
import { AppButton } from "../components/common/AppButton";
import { RevealSection } from "../components/common/RevealSection";
import { AuthCard } from "../components/auth/AuthCard";

type LoginPageProps = {
  mode: "login" | "register";
  username: string;
  password: string;
  error: string;
  onBack: () => void;
  onModeChange: (mode: "login" | "register") => void;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function LoginPage(props: LoginPageProps) {
  return (
    <div className="app-aurora min-h-screen text-white">
      <div className="app-aurora__wave app-aurora__wave--left" />
      <div className="app-aurora__wave app-aurora__wave--right" />
      <div className="app-aurora__grid" />
      <header className="border-b border-white/6 bg-black/30 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1680px] items-center justify-between gap-6 px-6 py-4">
          <div className="flex items-center gap-8">
            <span className="text-2xl font-black tracking-tight text-[#165DFF]">动能智投</span>
            <span className="hidden text-sm text-slate-500 xl:inline">登录后进入新能源汽车智能投研工作台</span>
          </div>
          <AppButton variant="ghost" onClick={props.onBack}>返回首页</AppButton>
        </div>
      </header>

      <div className="relative mx-auto min-h-[calc(100vh-73px)] max-w-[1680px] overflow-y-auto px-6 pb-12 pt-6 xl:flex xl:items-center">
        <div className="grid w-full items-center gap-10 xl:grid-cols-[minmax(340px,0.95fr)_minmax(360px,0.8fr)]">
          <RevealSection className="hidden xl:block" delayMs={40}>
            <section className="rounded-[32px] border border-white/8 bg-[radial-gradient(circle_at_top_left,rgba(22,93,255,0.12),transparent_26%),#111827] p-8 shadow-[0_24px_80px_rgba(0,0,0,0.28)]">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">登录前说明</p>
              <h1 className="mt-3 text-5xl font-black leading-tight text-white">面向新能源汽车赛道的智能投研入口</h1>
              <p className="mt-5 max-w-xl text-base leading-8 text-slate-300">当前平台聚焦股票分析、资讯舆情、趋势预测与后续个人投资管理模块。登录页尽量保持一屏完成，同时保留一点底部呼吸空间，让页面不显得过满。</p>
              <div className="mt-8 grid gap-4 md:grid-cols-2">
                <div className="rounded-[24px] border border-white/8 bg-[#151515] p-5">
                  <p className="text-sm font-semibold text-white">一屏优先登录</p>
                  <p className="mt-2 text-sm leading-7 text-slate-300">优先适配常见桌面屏幕，若高度不足则允许页内轻微滚动，避免按钮被截掉。</p>
                </div>
                <div className="rounded-[24px] border border-white/8 bg-[#151515] p-5">
                  <p className="text-sm font-semibold text-white">工作台聚焦效率</p>
                  <p className="mt-2 text-sm leading-7 text-slate-300">后续核心工作台保持三栏固定布局，图表优先，AI 仅作为辅助区。</p>
                </div>
              </div>
            </section>
          </RevealSection>

          <RevealSection className="flex justify-center xl:justify-end" delayMs={120}>
            <AuthCard
              mode={props.mode}
              username={props.username}
              password={props.password}
              error={props.error}
              onModeChange={props.onModeChange}
              onUsernameChange={props.onUsernameChange}
              onPasswordChange={props.onPasswordChange}
              onSubmit={props.onSubmit}
            />
          </RevealSection>
        </div>
      </div>
    </div>
  );
}
