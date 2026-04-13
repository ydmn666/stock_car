import type { FormEvent } from "react";
import { AppButton } from "../common/AppButton";

type AuthCardProps = {
  mode: "login" | "register";
  username: string;
  password: string;
  error: string;
  onModeChange: (mode: "login" | "register") => void;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function AuthCard(props: AuthCardProps) {
  return (
    <div className="glass-panel w-full max-w-[560px] rounded-[30px] p-7 xl:p-8">
      <div className="inline-flex rounded-full border border-[rgba(53,208,181,0.22)] bg-[rgba(53,208,181,0.08)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-[var(--color-accent)]">
        安全访问
      </div>
      <h1 className="mt-6 text-4xl font-black leading-tight text-[var(--color-text-strong)] xl:text-5xl">
        {props.mode === "login" ? "登录新能源汽车智能投研平台" : "创建新能源汽车智能投研账户"}
      </h1>
      <p className="mt-3 text-sm leading-7 text-[var(--color-text-muted)] xl:text-base">
        登录后即可进入核心工作台。当前版本聚焦股票分析、AI 问答与后续个人投资模块的统一入口。
      </p>

      <div className="mt-6 flex gap-3">
        <button onClick={() => props.onModeChange("login")} className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${props.mode === "login" ? "selected-chip" : "glass-chip text-[var(--color-text-muted)] hover:bg-white/85"}`}>
          登录
        </button>
        <button onClick={() => props.onModeChange("register")} className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${props.mode === "register" ? "selected-chip" : "glass-chip text-[var(--color-text-muted)] hover:bg-white/85"}`}>
          注册
        </button>
      </div>

      <form className="mt-6 space-y-4" onSubmit={props.onSubmit}>
        <label className="block">
          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">用户名</span>
          <input value={props.username} onChange={(event) => props.onUsernameChange(event.target.value)} className="data-card w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white xl:text-base" placeholder="请输入登录用户名" />
        </label>
        <label className="block">
          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">密码</span>
          <input type="password" value={props.password} onChange={(event) => props.onPasswordChange(event.target.value)} className="data-card w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white xl:text-base" placeholder="请输入密码" />
        </label>
        {props.error ? <p className="text-sm text-[var(--color-danger)]">{props.error}</p> : null}
        <AppButton type="submit" className="w-full py-3.5 text-base">{props.mode === "login" ? "进入核心工作台" : "创建并继续"}</AppButton>
      </form>
    </div>
  );
}
