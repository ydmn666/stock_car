import { type ButtonHTMLAttributes, type ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";

type AppButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: Variant;
};

export function AppButton({ children, variant = "primary", className = "", ...props }: AppButtonProps) {
  const variantClass =
    variant === "secondary"
      ? "border border-white/10 bg-white/6 text-white hover:border-[#165DFF]/30 hover:bg-white/10"
      : variant === "ghost"
        ? "border border-transparent bg-transparent text-slate-300 hover:bg-white/6"
        : "border border-[#165DFF] bg-[#165DFF] text-white hover:brightness-110";

  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-2xl px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${variantClass} ${className}`}
    >
      {children}
    </button>
  );
}
