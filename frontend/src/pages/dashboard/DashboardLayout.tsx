import { AppButton } from "../../components/common/AppButton";
import { RightAssistantPanel } from "../../components/assistant/RightAssistantPanel";
import { ContextHeader } from "../../components/dashboard/ContextHeader";
import { MetricStrip } from "../../components/dashboard/MetricStrip";
import type { WorkspaceTab } from "../../lib/workspace";
import { WORKSPACE_TABS } from "../../lib/workspace";
import type { StockOption } from "../../types";

type DashboardLayoutProps = {
  currentUser: string;
  health: string;
  activeTab: WorkspaceTab;
  activeStock: StockOption | null;
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
};

export function DashboardLayout(props: DashboardLayoutProps) {
  return (
    <div className="app-aurora h-screen overflow-hidden text-white">
      <div className="app-aurora__wave app-aurora__wave--left" />
      <div className="app-aurora__wave app-aurora__wave--right" />
      <div className="app-aurora__grid" />
      <header className="border-b border-white/6 bg-[#0b1220]/85 backdrop-blur">
        <div className="mx-auto flex max-w-[1920px] items-center justify-between gap-6 px-4 py-4 xl:px-6">
          <div className="flex items-center gap-8">
            <span className="text-2xl font-black tracking-tight text-[#165DFF]">动能智投</span>
            <nav className="hidden gap-7 text-sm text-slate-500 xl:flex">
              <span className="text-white">新能源汽车智能投研工作台</span>
              <span>多市场分析</span>
              <span>AI 辅助问答</span>
              <span>个人投资模块预留</span>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden rounded-full border border-white/8 px-3 py-2 text-xs text-slate-400 xl:inline-flex">{props.currentUser || "访客"} · {props.health === "ok" ? "系统在线" : "系统检测中"}</span>
            <AppButton variant="secondary" onClick={props.onBackToSetup}>重新配置</AppButton>
            <AppButton variant="secondary" onClick={() => void props.onExportPdf()} disabled={props.exportDisabled}>导出报告</AppButton>
            <AppButton variant="ghost" onClick={props.onLogout}>退出</AppButton>
          </div>
        </div>
      </header>

      <div className="relative mx-auto grid h-[calc(100vh-73px)] max-w-[1920px] gap-4 overflow-hidden px-4 py-4 xl:grid-cols-[170px_minmax(0,1fr)_390px] 2xl:grid-cols-[190px_minmax(0,1fr)_430px] xl:px-6 xl:py-5">
        <aside className="hidden h-full min-h-0 xl:block">
          <div className="h-full overflow-y-auto overscroll-contain pr-1">
            <div className="space-y-2">
              {WORKSPACE_TABS.map((item) => (
                <button key={item.key} type="button" onClick={() => props.onTabChange(item.key)} className={`flex w-full items-center justify-between rounded-2xl px-4 py-3 text-left text-sm font-medium transition ${props.activeTab === item.key ? "bg-[#165DFF] text-white" : "border border-white/8 bg-[#111827] text-slate-300 hover:border-[#165DFF]/30 hover:bg-[#165DFF]/10"}`}>
                  <span>{item.label}</span>
                  <span className={`text-xs ${props.activeTab === item.key ? "text-white/70" : "text-slate-500"}`}>{item.short}</span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        <main className="min-w-0 min-h-0 overflow-y-auto overscroll-contain pr-1">
          <div className="space-y-4 pb-6">
            <ContextHeader
              activeStock={props.activeStock}
              startDate={props.startDate}
              endDate={props.endDate}
              actions={
                <>
                  <AppButton variant="secondary" onClick={props.onBackToSetup}>切换股票</AppButton>
                  <AppButton onClick={() => void props.onExportPdf()} disabled={props.exportDisabled}>生成当前报告</AppButton>
                </>
              }
            />
            <MetricStrip items={props.metricItems} />
            <section>{props.moduleContent}</section>
          </div>
        </main>

        <aside className="hidden h-full min-h-0 xl:block">
          <RightAssistantPanel
            currentUser={props.currentUser}
            context={props.assistantContext}
            prompts={["总结当前股票的走势特点", "解释这段时间收益变化原因", "基于新闻给出一个风险提示", "帮我概括当前页面重点"]}
            onRequestPdf={props.onExportPdf}
          />
        </aside>
      </div>
    </div>
  );
}
