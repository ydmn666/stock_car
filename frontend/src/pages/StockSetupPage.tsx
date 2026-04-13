import { AppButton } from "../components/common/AppButton";
import { RevealSection } from "../components/common/RevealSection";
import type { SetupMarket } from "../lib/workspace";
import type { Instrument } from "../types";

type StockSetupPageProps = {
  currentUser: string;
  market: SetupMarket;
  selectedStocks: Instrument[];
  activeCode: string;
  manualCode: string;
  manualError: string;
  startDate: string;
  endDate: string;
  loading: boolean;
  workspaceError: string;
  onBack: () => void;
  onProceed: () => void;
  onMarketChange: (value: SetupMarket) => void;
  onManualCodeChange: (value: string) => void;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onSetActiveCode: (value: string) => void;
  onAddStock: (stock: Instrument) => void;
  onAddManualStock: () => void;
  onRemoveStock: (code: string) => void;
  hotStocks: Instrument[];
};

const MARKET_OPTIONS: Array<{ key: SetupMarket; label: string; hint: string }> = [
  { key: "cn", label: "A 股", hint: "聚焦新能源整车、电池、零部件与产业链核心标的" },
];

export function StockSetupPage(props: StockSetupPageProps) {
  return (
    <div className="app-aurora min-h-screen text-[var(--color-text)]">
      <div className="app-aurora__wave app-aurora__wave--left" />
      <div className="app-aurora__wave app-aurora__wave--right" />
      <div className="app-aurora__grid" />
      <header className="border-b border-[var(--color-border)] bg-[rgba(255,255,255,0.62)] backdrop-blur">
        <div className="mx-auto flex max-w-[1800px] items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-6">
            <span className="text-2xl font-black tracking-tight text-[var(--color-primary)]">动能智投</span>
            <p className="hidden text-sm text-[var(--color-text-muted)] xl:block">先完成选股与分析区间配置，再进入核心工作台</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="glass-chip hidden rounded-full px-3 py-2 text-xs text-[var(--color-text-muted)] xl:inline-flex">{props.currentUser || "访客"} · 分析配置中</span>
            <AppButton variant="ghost" onClick={props.onBack}>返回登录</AppButton>
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-[1800px] px-5 py-5">
        <section className="glass-panel-soft overflow-hidden rounded-[32px] p-6">
          <div className="grid gap-5 xl:grid-rows-[auto_auto_1fr]">
            <RevealSection>
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-muted)]">分析配置页</p>
                <h1 className="mt-3 max-w-5xl text-4xl font-black leading-tight text-[var(--color-text-strong)] xl:text-5xl">先定义本轮 A 股分析上下文，再进入新能源汽车智能投研工作台</h1>
                <p className="mt-4 max-w-4xl text-sm leading-7 text-[var(--color-text-muted)] xl:text-base xl:leading-8">这里负责统一选择 A 股股票与时间区间。后续总览、技术分析、资讯舆情、趋势预测都会共享这份上下文，避免工作台内重复配置。</p>
              </div>
            </RevealSection>

            <RevealSection delayMs={80} className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {MARKET_OPTIONS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => props.onMarketChange(item.key)}
                  className={`rounded-[24px] border px-5 py-5 text-left transition ${props.market === item.key ? "selected-card" : "glass-panel hover:bg-white/85"}`}
                >
                  <div className="text-lg font-semibold text-[var(--color-text-strong)]">{item.label}</div>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-text-muted)]">{item.hint}</p>
                </button>
              ))}
            </RevealSection>

            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
              <RevealSection delayMs={140} className="glass-panel overflow-hidden rounded-[28px] p-5">
                <div className="flex flex-col">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-muted)]">股票列表</p>
                      <h2 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">选择本轮关注标的</h2>
                    </div>
                    <span className="glass-chip rounded-full px-3 py-2 text-xs text-[var(--color-text-muted)]">当前 {props.selectedStocks.length} / 5</span>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {props.hotStocks.map((stock) => {
                      const selected = props.selectedStocks.some((item) => item.id === stock.id);
                      return (
                        <button
                          key={stock.id}
                          type="button"
                          onClick={() => props.onAddStock(stock)}
                          className={`rounded-full px-4 py-2 text-sm transition ${selected ? "selected-chip font-semibold" : "glass-chip text-[var(--color-text-muted)] hover:bg-white/85"}`}
                        >
                          {stock.display_name}
                        </button>
                      );
                    })}
                    {!props.hotStocks.length ? <p className="text-sm text-[var(--color-text-muted)]">当前市场预置股票为空，你也可以直接手动输入代码添加。</p> : null}
                  </div>

                  <div className="mt-4 flex gap-2">
                    <input
                      value={props.manualCode}
                      onChange={(event) => props.onManualCodeChange(event.target.value)}
                      placeholder="输入 A 股代码，例如 002594 / 300750"
                      className="data-card min-w-0 flex-1 rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white"
                    />
                    <AppButton variant="secondary" onClick={props.onAddManualStock}>添加</AppButton>
                  </div>
                  {props.manualError ? <p className="mt-2 text-sm text-[var(--color-danger)]">{props.manualError}</p> : null}

                  <div className="mt-4 max-h-[360px] overflow-y-auto pr-1">
                    <div className="grid gap-3 md:grid-cols-2">
                      {props.selectedStocks.map((stock) => (
                        <div key={stock.id} className={`rounded-[24px] border px-4 py-4 transition ${stock.id === props.activeCode ? "selected-card" : "content-card"}`}>
                          <button type="button" className="w-full text-left" onClick={() => props.onSetActiveCode(stock.id)}>
                            <div className="font-medium text-[var(--color-text-strong)]">{stock.display_name}</div>
                            <div className="mt-1 text-xs text-[var(--color-text-soft)]">{stock.full_symbol}</div>
                          </button>
                          <button type="button" onClick={() => props.onRemoveStock(stock.id)} className="mt-3 text-xs text-[var(--color-text-muted)] transition hover:text-[var(--color-danger)]">从本轮分析中移除</button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </RevealSection>

              <RevealSection delayMs={180} className="glass-panel rounded-[28px] p-5">
                <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-muted)]">配置摘要</p>
                <h2 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">锁定时间与分析入口</h2>

                <div className="mt-5 space-y-4">
                  <label className="block">
                    <span className="mb-2 block text-xs text-[var(--color-text-muted)]">开始日期</span>
                    <input type="date" value={props.startDate} onChange={(event) => props.onStartDateChange(event.target.value)} className="data-card w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white" />
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-xs text-[var(--color-text-muted)]">结束日期</span>
                    <input type="date" value={props.endDate} onChange={(event) => props.onEndDateChange(event.target.value)} className="data-card w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white" />
                  </label>
                </div>

                <div className="data-card rounded-[24px] mt-5 p-4">
                  <div className="text-sm text-[var(--color-text-muted)]">当前主标的</div>
                  <div className="mt-2 text-xl font-semibold text-[var(--color-text-strong)]">{props.selectedStocks.find((item) => item.id === props.activeCode)?.display_name ?? "尚未设置"}</div>
                  <div className="mt-1 text-sm text-[var(--color-text-muted)]">{props.selectedStocks.find((item) => item.id === props.activeCode)?.full_symbol ?? "请先选择股票"}</div>
                </div>

                <div className="content-card rounded-[24px] mt-4 p-4">
                  <div className="text-sm text-[var(--color-text-muted)]">进入工作台后可查看</div>
                  <ul className="mt-3 space-y-2 text-sm leading-7 text-[var(--color-text-muted)]">
                    <li>总览与多股票收益对比</li>
                    <li>市场分析与技术图表轮播</li>
                    <li>资讯舆情、趋势预测与历史记录</li>
                  </ul>
                </div>

                {props.workspaceError ? <p className="mt-4 text-sm text-[var(--color-danger)]">{props.workspaceError}</p> : null}

                <AppButton className="mt-5 w-full" onClick={props.onProceed} disabled={props.loading || !props.selectedStocks.length}>{props.loading ? "正在加载分析数据..." : "进入核心工作台"}</AppButton>
              </RevealSection>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

