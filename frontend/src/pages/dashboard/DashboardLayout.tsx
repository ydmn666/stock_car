import { AppButton } from "../../components/common/AppButton";
import { RightAssistantPanel } from "../../components/assistant/RightAssistantPanel";
import { ContextHeader } from "../../components/dashboard/ContextHeader";
import { MetricStrip } from "../../components/dashboard/MetricStrip";
import type { WorkspaceTab } from "../../lib/workspace";
import { WORKSPACE_TABS } from "../../lib/workspace";
import type { Instrument } from "../../types";

type DashboardLayoutProps = {
  currentUser: string;
  health: string;
  activeTab: WorkspaceTab;
  activeStock: Instrument | null;
  startDate: string;
  endDate: string;
  metricItems: Array<{ label: string; value: string; hint?: string; tone?: "green" | "yellow" | "gray" }>;
  assistantContext: Record<string, unknown>;
  moduleContent: React.ReactNode;
  onTabChange: (tab: WorkspaceTab) => void;
  onBackToSetup: () => void;
  onLogout: () => void;
  onExportPdf: () => Promise<boolean | void>;
  exportDisabled: boolean;
  exportLoading: boolean;
  exportStatus: string;
  workspaceError: string;
};

export function DashboardLayout(props: DashboardLayoutProps) {
  const isAnalysisContext = !["portfolio", "history"].includes(props.activeTab);

  return (
    <div className="app-aurora h-screen overflow-hidden text-[var(--color-text)]">
      <div className="app-aurora__wave app-aurora__wave--left" />
      <div className="app-aurora__wave app-aurora__wave--right" />
      <div className="app-aurora__grid" />
      <header className="border-b border-[var(--color-border)] bg-[rgba(255,255,255,0.62)] backdrop-blur">
        <div className="mx-auto flex max-w-[1920px] items-center justify-between gap-6 px-4 py-4 xl:px-6">
          <div className="flex items-center gap-8">
            <span className="text-2xl font-black tracking-tight text-[var(--color-primary)]">动能智投</span>
            <nav className="hidden gap-7 text-sm text-[var(--color-text-muted)] xl:flex">
              <span className="text-[var(--color-text-strong)]">新能源汽车智能投研工作台</span>
              <span>A 股深度分析</span>
              <span>AI 辅助问答</span>
              <span>个人投资模块预留</span>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="glass-chip hidden rounded-full px-3 py-2 text-xs text-[var(--color-text-muted)] xl:inline-flex">{props.currentUser || "访客"} · {props.health === "ok" ? "系统在线" : "系统检测中"}</span>
            <AppButton variant="secondary" onClick={props.onBackToSetup}>重新配置</AppButton>
            {isAnalysisContext ? (
              <AppButton variant="secondary" onClick={() => void props.onExportPdf()} disabled={props.exportDisabled || props.exportLoading}>
                {props.exportLoading ? "正在生成报告..." : "导出报告"}
              </AppButton>
            ) : null}
            <AppButton variant="ghost" onClick={props.onLogout}>退出</AppButton>
          </div>
        </div>
      </header>

      <div className="relative mx-auto grid h-[calc(100vh-73px)] max-w-[1920px] gap-4 overflow-hidden px-4 py-4 xl:grid-cols-[170px_minmax(0,1fr)_380px] 2xl:grid-cols-[190px_minmax(0,1fr)_410px] xl:px-6 xl:py-5">
        <aside className="hidden h-full min-h-0 xl:block">
          <div className="h-full overflow-y-auto overscroll-contain pr-1">
            <div className="space-y-2">
              {WORKSPACE_TABS.map((item) => (
                <button key={item.key} type="button" onClick={() => props.onTabChange(item.key)} className={`flex w-full items-center justify-between rounded-[22px] px-4 py-3 text-left text-sm font-medium transition ${props.activeTab === item.key ? "selected-card text-[var(--color-text-strong)]" : "glass-panel text-[var(--color-text-strong)] hover:border-[color:var(--color-primary-border)] hover:bg-white/85"}`}>
                  <span>{item.label}</span>
                  <span className={`text-xs ${props.activeTab === item.key ? "text-[var(--color-primary)]" : "text-[var(--color-text-soft)]"}`}>{item.short}</span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        <main className="min-w-0 min-h-0 overflow-y-auto overscroll-contain pr-1">
          <div className="space-y-4 pb-6">
            {isAnalysisContext ? (
              <ContextHeader
                activeStock={props.activeStock}
                startDate={props.startDate}
                endDate={props.endDate}
                actions={
                  <>
                    <AppButton variant="secondary" onClick={props.onBackToSetup}>切换股票</AppButton>
                    <AppButton onClick={() => void props.onExportPdf()} disabled={props.exportDisabled || props.exportLoading}>
                      {props.exportLoading ? "正在生成报告..." : "生成当前报告"}
                    </AppButton>
                  </>
                }
              />
            ) : null}
            {isAnalysisContext && props.exportStatus ? <div className="glass-panel rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)]">{props.exportStatus}</div> : null}
            {props.workspaceError ? <div className="rounded-2xl border border-[rgba(240,107,116,0.22)] bg-[rgba(240,107,116,0.1)] px-4 py-3 text-sm text-[var(--color-danger)]">{props.workspaceError}</div> : null}
            {isAnalysisContext ? <MetricStrip items={props.metricItems} /> : null}
            <section>{props.moduleContent}</section>
          </div>
        </main>

        <aside className="hidden h-full min-h-0 xl:block">
          <div className="sticky top-0 flex h-full max-h-full items-start pt-0 pb-3">
            <RightAssistantPanel
              currentUser={props.currentUser}
              context={props.assistantContext}
              prompts={["总结当前股票的走势特点", "解释这段时间收益变化原因", "基于新闻给出一个风险提示", "帮我概括当前页面重点"]}
              onRequestPdf={props.onExportPdf}
            />
          </div>
        </aside>
      </div>
    </div>
  );
}

