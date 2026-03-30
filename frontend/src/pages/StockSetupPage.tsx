import { AppButton } from "../components/common/AppButton";
import { RevealSection } from "../components/common/RevealSection";
import type { SetupMarket } from "../lib/workspace";
import type { StockOption } from "../types";

type StockSetupPageProps = {
  currentUser: string;
  market: SetupMarket;
  selectedStocks: StockOption[];
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
  onAddStock: (stock: StockOption) => void;
  onAddManualStock: () => void;
  onRemoveStock: (code: string) => void;
  hotStocks: StockOption[];
};

const MARKET_OPTIONS: Array<{ key: SetupMarket; label: string; hint: string }> = [
  { key: "all", label: "跨市场", hint: "同时面向 A 股、美股、港股的代表性标的" },
  { key: "cn", label: "A 股", hint: "优先关注新能源整车、电池、零部件" },
  { key: "us", label: "美股", hint: "适合追踪特斯拉、Rivian、充电网络等标的" },
  { key: "hk", label: "港股", hint: "补充港股新能源车企与产业链公司" },
];

export function StockSetupPage(props: StockSetupPageProps) {
  return (
    <div className="app-aurora min-h-screen text-white">
      <div className="app-aurora__wave app-aurora__wave--left" />
      <div className="app-aurora__wave app-aurora__wave--right" />
      <div className="app-aurora__grid" />
      <header className="border-b border-white/6 bg-black/30 backdrop-blur">
        <div className="mx-auto flex max-w-[1800px] items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-6">
            <span className="text-2xl font-black tracking-tight text-[#165DFF]">动能智投</span>
            <p className="hidden text-sm text-slate-500 xl:block">先完成选股与分析区间配置，再进入核心工作台</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden rounded-full border border-white/8 px-3 py-2 text-xs text-slate-400 xl:inline-flex">{props.currentUser || "访客"} · 分析配置中</span>
            <AppButton variant="ghost" onClick={props.onBack}>返回登录</AppButton>
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-[1800px] px-5 py-5">
        <section className="overflow-hidden rounded-[32px] border border-white/8 bg-[radial-gradient(circle_at_top_left,rgba(22,93,255,0.12),transparent_24%),#121212] p-6">
          <div className="grid gap-5 xl:grid-rows-[auto_auto_1fr]">
            <RevealSection>
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">分析配置页</p>
                <h1 className="mt-3 max-w-5xl text-4xl font-black leading-tight text-white xl:text-5xl">先定义本轮分析上下文，再进入新能源汽车智能投研工作台</h1>
                <p className="mt-4 max-w-4xl text-sm leading-7 text-slate-300 xl:text-base xl:leading-8">这里负责统一选择市场、股票与时间区间。后续总览、技术分析、资讯舆情、趋势预测都会共享这份上下文，避免工作台内重复配置。</p>
              </div>
            </RevealSection>

            <RevealSection delayMs={80} className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {MARKET_OPTIONS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => props.onMarketChange(item.key)}
                  className={`rounded-[24px] border px-5 py-5 text-left transition ${props.market === item.key ? "border-[#165DFF]/30 bg-[#165DFF]/10" : "border-white/8 bg-[#171717] hover:bg-white/5"}`}
                >
                  <div className="text-lg font-semibold text-white">{item.label}</div>
                  <p className="mt-2 text-sm leading-7 text-slate-300">{item.hint}</p>
                </button>
              ))}
            </RevealSection>

            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
              <RevealSection delayMs={140} className="overflow-hidden rounded-[28px] border border-white/8 bg-[#151515] p-5">
                <div className="flex flex-col">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.22em] text-slate-500">股票列表</p>
                      <h2 className="mt-2 text-2xl font-semibold text-white">选择本轮关注标的</h2>
                    </div>
                    <span className="rounded-full border border-white/8 bg-white/4 px-3 py-2 text-xs text-slate-400">当前 {props.selectedStocks.length} / 5</span>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {props.hotStocks.map((stock) => {
                      const selected = props.selectedStocks.some((item) => item.code === stock.code);
                      return (
                        <button
                          key={stock.code}
                          type="button"
                          onClick={() => props.onAddStock(stock)}
                          className={`rounded-full px-4 py-2 text-sm transition ${selected ? "bg-[#165DFF] text-white" : "border border-white/8 bg-white/4 text-zinc-300 hover:bg-white/8"}`}
                        >
                          {stock.name}
                        </button>
                      );
                    })}
                    {!props.hotStocks.length ? <p className="text-sm text-slate-500">当前市场预置股票为空，你也可以直接手动输入代码添加。</p> : null}
                  </div>

                  <div className="mt-4 flex gap-2">
                    <input
                      value={props.manualCode}
                      onChange={(event) => props.onManualCodeChange(event.target.value)}
                      placeholder="输入股票代码，例如 TSLA / 002594 / 1211.HK"
                      className="min-w-0 flex-1 rounded-2xl border border-white/8 bg-[#0d0d0d] px-4 py-3 text-sm text-white outline-none transition focus:border-[#165DFF]/40"
                    />
                    <AppButton variant="secondary" onClick={props.onAddManualStock}>添加</AppButton>
                  </div>
                  {props.manualError ? <p className="mt-2 text-sm text-[#F87272]">{props.manualError}</p> : null}

                  <div className="mt-4 max-h-[360px] overflow-y-auto pr-1">
                    <div className="grid gap-3 md:grid-cols-2">
                      {props.selectedStocks.map((stock) => (
                        <div key={stock.code} className={`rounded-[24px] border px-4 py-4 transition ${stock.code === props.activeCode ? "border-[#165DFF]/30 bg-[#165DFF]/10" : "border-white/8 bg-[#101010]"}`}>
                          <button type="button" className="w-full text-left" onClick={() => props.onSetActiveCode(stock.code)}>
                            <div className="font-medium text-white">{stock.name}</div>
                            <div className="mt-1 text-xs text-slate-500">{stock.code}</div>
                          </button>
                          <button type="button" onClick={() => props.onRemoveStock(stock.code)} className="mt-3 text-xs text-slate-500 transition hover:text-[#F87272]">从本轮分析中移除</button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </RevealSection>

              <RevealSection delayMs={180} className="rounded-[28px] border border-white/8 bg-[#151515] p-5">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">配置摘要</p>
                <h2 className="mt-2 text-2xl font-semibold text-white">锁定时间与分析入口</h2>

                <div className="mt-5 space-y-4">
                  <label className="block">
                    <span className="mb-2 block text-xs text-slate-500">开始日期</span>
                    <input type="date" value={props.startDate} onChange={(event) => props.onStartDateChange(event.target.value)} className="w-full rounded-2xl border border-white/8 bg-[#0d0d0d] px-4 py-3 text-sm text-white outline-none transition focus:border-[#165DFF]/40" />
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-xs text-slate-500">结束日期</span>
                    <input type="date" value={props.endDate} onChange={(event) => props.onEndDateChange(event.target.value)} className="w-full rounded-2xl border border-white/8 bg-[#0d0d0d] px-4 py-3 text-sm text-white outline-none transition focus:border-[#165DFF]/40" />
                  </label>
                </div>

                <div className="mt-5 rounded-[24px] border border-white/8 bg-[#101010] p-4">
                  <div className="text-sm text-slate-500">当前主标的</div>
                  <div className="mt-2 text-xl font-semibold text-white">{props.selectedStocks.find((item) => item.code === props.activeCode)?.name ?? "尚未设置"}</div>
                  <div className="mt-1 text-sm text-slate-500">{props.activeCode || "请先选择股票"}</div>
                </div>

                <div className="mt-4 rounded-[24px] border border-white/8 bg-[#101010] p-4">
                  <div className="text-sm text-slate-500">进入工作台后可查看</div>
                  <ul className="mt-3 space-y-2 text-sm leading-7 text-zinc-300">
                    <li>总览与多股票收益对比</li>
                    <li>市场分析与技术图表轮播</li>
                    <li>资讯舆情、趋势预测与历史记录</li>
                  </ul>
                </div>

                {props.workspaceError ? <p className="mt-4 text-sm text-[#F87272]">{props.workspaceError}</p> : null}

                <AppButton className="mt-5 w-full" onClick={props.onProceed} disabled={props.loading || !props.selectedStocks.length}>{props.loading ? "正在加载分析数据..." : "进入核心工作台"}</AppButton>
              </RevealSection>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
