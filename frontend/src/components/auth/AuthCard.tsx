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
    <div className="w-full max-w-[560px] rounded-[30px] border border-white/8 bg-[radial-gradient(circle_at_top,rgba(22,93,255,0.12),transparent_32%),#111827] p-7 shadow-[0_30px_120px_rgba(2,6,23,0.45)] xl:p-8">
      <div className="inline-flex rounded-full border border-[#36D399]/25 bg-[#36D399]/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-[#36D399]">
        安全访问
      </div>
      <h1 className="mt-6 text-4xl font-black leading-tight text-white xl:text-5xl">
        {props.mode === "login" ? "登录新能源汽车智能投研平台" : "创建新能源汽车智能投研账户"}
      </h1>
      <p className="mt-3 text-sm leading-7 text-slate-300 xl:text-base">
        登录后即可进入核心工作台。当前版本聚焦股票分析、AI 问答与后续个人投资模块的统一入口。
      </p>

      <div className="mt-6 flex gap-3">
        <button onClick={() => props.onModeChange("login")} className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${props.mode === "login" ? "bg-[#165DFF] text-white" : "bg-white/6 text-slate-300 hover:bg-white/10"}`}>
          登录
        </button>
        <button onClick={() => props.onModeChange("register")} className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${props.mode === "register" ? "bg-[#165DFF] text-white" : "bg-white/6 text-slate-300 hover:bg-white/10"}`}>
          注册
        </button>
      </div>

      <form className="mt-6 space-y-4" onSubmit={props.onSubmit}>
        <label className="block">
          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">用户名</span>
          <input value={props.username} onChange={(event) => props.onUsernameChange(event.target.value)} className="w-full rounded-2xl border border-white/8 bg-[#0b1220] px-4 py-3 text-sm text-white outline-none transition focus:border-[#165DFF]/50 xl:text-base" placeholder="请输入登录用户名" />
        </label>
        <label className="block">
          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">密码</span>
          <input type="password" value={props.password} onChange={(event) => props.onPasswordChange(event.target.value)} className="w-full rounded-2xl border border-white/8 bg-[#0b1220] px-4 py-3 text-sm text-white outline-none transition focus:border-[#165DFF]/50 xl:text-base" placeholder="请输入密码" />
        </label>
        {props.error ? <p className="text-sm text-[#F87272]">{props.error}</p> : null}
        <AppButton type="submit" className="w-full py-3.5 text-base">{props.mode === "login" ? "进入核心工作台" : "创建并继续"}</AppButton>
      </form>
    </div>
  );
}
