import { type ButtonHTMLAttributes, type ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";

type AppButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: Variant;
};

export function AppButton({ children, variant = "primary", className = "", ...props }: AppButtonProps) {
  const variantClass =
    variant === "secondary"
      ? "border border-[var(--color-border)] bg-[rgba(255,255,255,0.82)] text-[var(--color-text)] shadow-[0_8px_22px_rgba(80,140,170,0.06)] backdrop-blur-[16px] hover:border-[color:var(--color-primary-border)] hover:bg-white/90"
      : variant === "ghost"
        ? "border border-transparent bg-transparent text-[var(--color-text-muted)] hover:bg-white/45"
        : "border border-[rgba(34,193,220,0.28)] bg-[rgba(34,193,220,0.94)] text-white shadow-[0_10px_24px_rgba(34,193,220,0.18)] hover:bg-[var(--color-primary-hover)] active:bg-[var(--color-primary-active)]";

  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-2xl px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${variantClass} ${className}`}
    >
      {children}
    </button>
  );
}
