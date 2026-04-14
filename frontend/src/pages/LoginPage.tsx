import type { FormEvent } from "react";
import { AppButton } from "../components/common/AppButton";
import { RevealSection } from "../components/common/RevealSection";
import { AuthCard } from "../components/auth/AuthCard";

type LoginPageProps = {
  mode: "login" | "register";
  username: string;
  password: string;
  confirmPassword: string;
  error: string;
  onBack: () => void;
  onModeChange: (mode: "login" | "register") => void;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onConfirmPasswordChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function LoginPage(props: LoginPageProps) {
  return (
    <div className="app-aurora min-h-screen text-[var(--color-text)]">
      <div className="app-aurora__wave app-aurora__wave--left" />
      <div className="app-aurora__wave app-aurora__wave--right" />
      <div className="app-aurora__grid" />
      <header className="border-b border-[var(--color-border)] bg-[rgba(255,255,255,0.62)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1680px] items-center justify-between gap-6 px-6 py-4">
          <div className="flex items-center gap-8">
            <span className="text-2xl font-black tracking-tight text-[var(--color-primary)]">动能智投</span>
            <span className="hidden text-sm text-[var(--color-text-muted)] xl:inline">登录后进入新能源汽车智能投研工作台</span>
          </div>
          <AppButton variant="ghost" onClick={props.onBack}>返回首页</AppButton>
        </div>
      </header>

      <div className="relative mx-auto min-h-[calc(100vh-73px)] max-w-[1680px] overflow-y-auto px-6 pb-12 pt-6 xl:flex xl:items-center">
        <div className="grid w-full items-center gap-10 xl:grid-cols-[minmax(340px,0.95fr)_minmax(360px,0.8fr)]">
          <RevealSection className="hidden xl:block" delayMs={40}>
            <section className="glass-panel-soft rounded-[32px] p-8">
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--color-text-soft)]">登录前说明</p>
              <h1 className="mt-3 text-5xl font-black leading-tight text-[var(--color-text-strong)]">面向新能源汽车赛道的智能投研入口</h1>
              <p className="mt-5 max-w-xl text-base leading-8 text-[var(--color-text-muted)]">当前平台聚焦股票分析、资讯舆情、趋势预测与后续个人投资管理模块。登录页尽量保持一屏完成，同时保留一点底部呼吸空间，让页面不显得过满。</p>
              <div className="mt-8 grid gap-4 md:grid-cols-2">
                <div className="content-card rounded-[24px] p-5">
                  <p className="text-sm font-semibold text-[var(--color-text-strong)]">一屏优先登录</p>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-text-muted)]">优先适配常见桌面屏幕，若高度不足则允许页内轻微滚动，避免按钮被截掉。</p>
                </div>
                <div className="content-card rounded-[24px] p-5">
                  <p className="text-sm font-semibold text-[var(--color-text-strong)]">工作台聚焦效率</p>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-text-muted)]">后续核心工作台保持三栏固定布局，图表优先，AI 仅作为辅助区。</p>
                </div>
              </div>
            </section>
          </RevealSection>

          <RevealSection className="flex justify-center xl:justify-end" delayMs={120}>
            <AuthCard
              mode={props.mode}
              username={props.username}
              password={props.password}
              confirmPassword={props.confirmPassword}
              error={props.error}
              onModeChange={props.onModeChange}
              onUsernameChange={props.onUsernameChange}
              onPasswordChange={props.onPasswordChange}
              onConfirmPasswordChange={props.onConfirmPasswordChange}
              onSubmit={props.onSubmit}
            />
          </RevealSection>
        </div>
      </div>
    </div>
  );
}
