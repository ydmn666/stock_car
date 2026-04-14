import { type FormEvent, useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import { AppButton } from "../../components/common/AppButton";
import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";
import {
  changePassword,
  createPortfolioTransaction,
  deletePortfolioTransaction,
  getPortfolioPerformance,
  getPortfolioPositions,
  getPortfolioSummary,
  getPortfolioTransactions,
  updatePortfolioTransaction,
} from "../../lib/api";
import { money, percent } from "../../lib/workspace";
import type {
  PortfolioAllocationItem,
  PortfolioPerformancePoint,
  PortfolioPosition,
  PortfolioSummary,
  PortfolioTransaction,
} from "../../types";

type PortfolioPageProps = {
  currentUser: string;
};

type PortfolioSubTab = "summary" | "positions" | "transactions" | "performance";

const SUB_TABS: Array<{ key: PortfolioSubTab; label: string; short: string }> = [
  { key: "summary", label: "账户概览", short: "概" },
  { key: "positions", label: "当前持仓", short: "仓" },
  { key: "transactions", label: "交易记录", short: "记" },
  { key: "performance", label: "收益分析", short: "益" },
];

const EMPTY_SUMMARY: PortfolioSummary = {
  total_buy_amount: 0,
  total_sell_amount: 0,
  total_fees: 0,
  net_invested: 0,
  cash_returned: 0,
  realized_pnl: 0,
  holding_cost: 0,
  market_value: 0,
  unrealized_pnl: 0,
  unrealized_pnl_pct: null,
  position_count: 0,
  transaction_count: 0,
};

function SectionShell(props: { eyebrow: string; title: string; description: string; actions?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="glass-panel rounded-[28px] p-5">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-text-soft)]">{props.eyebrow}</p>
          <h3 className="mt-2 text-2xl font-semibold text-[var(--color-text-strong)]">{props.title}</h3>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--color-text-muted)]">{props.description}</p>
        </div>
        {props.actions ? <div className="flex flex-wrap gap-3">{props.actions}</div> : null}
      </div>
      {props.children}
    </section>
  );
}

function SummaryCards(props: { summary: PortfolioSummary }) {
  const isFlat = props.summary.position_count === 0;
  const isNetCashReturned = !isFlat && props.summary.net_invested < 0;
  const cards = [
    { label: "累计买入", value: money(props.summary.total_buy_amount), hint: "历史买入成交金额合计" },
    { label: "累计卖出", value: money(props.summary.total_sell_amount), hint: "历史卖出成交金额合计" },
    {
      label: isFlat ? "已实现盈亏" : "当前持仓成本",
      value: money(isFlat ? props.summary.realized_pnl : props.summary.holding_cost),
      hint: isFlat ? "当前已无持仓，展示累计已实现结果" : "仍在持有仓位的成本合计",
    },
    {
      label: isFlat ? "回笼资金" : "浮动盈亏",
      value: money(isFlat ? props.summary.cash_returned : props.summary.unrealized_pnl),
      hint: isFlat ? "卖出后累计回收的资金" : props.summary.unrealized_pnl_pct == null ? "暂无可计算收益率" : percent(props.summary.unrealized_pnl_pct),
    },
    ...(isNetCashReturned
      ? [
          {
            label: "累计净回笼",
            value: money(Math.abs(props.summary.net_invested)),
            hint: "累计卖出已超过累计买入，当前持仓相当于利润仓",
          },
        ]
      : []),
  ];

  return (
    <div className={`grid gap-3 lg:grid-cols-2 ${cards.length > 4 ? "xl:grid-cols-5" : "xl:grid-cols-4"}`}>
      {cards.map((item) => (
        <div key={item.label} className="data-card rounded-[24px] px-5 py-4">
          <p className="text-sm text-[var(--color-text-soft)]">{item.label}</p>
          <p className="mt-3 break-all text-[2rem] font-semibold leading-tight text-[var(--color-text-strong)] xl:text-[2.2rem]">{item.value}</p>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">{item.hint}</p>
        </div>
      ))}
    </div>
  );
}

function PositionsTable(props: { items: PortfolioPosition[] }) {
  if (!props.items.length) {
    return <EmptyStatePanel title="当前还没有持仓" description="先去交易记录里新增一笔买入，系统就会开始汇总当前持仓。" />;
  }

  return (
    <div className="glass-panel max-h-[620px] overflow-auto overscroll-contain rounded-[22px]">
      <table className="min-w-[980px] text-sm">
        <thead className="sticky top-0 z-10 bg-[rgba(255,255,255,0.8)] text-[var(--color-text-soft)] backdrop-blur-[14px]">
          <tr>
            {["股票", "持仓股数", "成本价", "持仓成本", "最新价", "当前市值", "浮动盈亏", "收益率"].map((label) => (
              <th key={label} className="whitespace-nowrap px-4 py-3 text-left font-medium">{label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(216,236,242,0.8)] text-[var(--color-text)]">
          {props.items.map((item) => (
            <tr key={item.symbol}>
              <td className="px-4 py-3">
                <div className="font-medium text-[var(--color-text-strong)]">{item.stock_name}</div>
                <div className="mt-1 text-xs text-[var(--color-text-soft)]">{item.symbol}</div>
              </td>
              <td className="whitespace-nowrap px-4 py-3">{item.quantity.toLocaleString("zh-CN")}</td>
              <td className="whitespace-nowrap px-4 py-3">{money(item.avg_cost)}</td>
              <td className="whitespace-nowrap px-4 py-3">{money(item.cost_basis)}</td>
              <td className="whitespace-nowrap px-4 py-3">{money(item.latest_price)}</td>
              <td className="whitespace-nowrap px-4 py-3">{money(item.market_value)}</td>
              <td className={`whitespace-nowrap px-4 py-3 ${(item.unrealized_pnl ?? 0) >= 0 ? "text-[var(--color-profit)]" : "text-[var(--color-risk)]"}`}>{money(item.unrealized_pnl)}</td>
              <td className={`whitespace-nowrap px-4 py-3 ${(item.unrealized_pnl_pct ?? 0) >= 0 ? "text-[var(--color-profit)]" : "text-[var(--color-risk)]"}`}>{percent(item.unrealized_pnl_pct)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TransactionsTable(props: {
  items: PortfolioTransaction[];
  deletingId: number | null;
  editingId: number | null;
  onDelete: (id: number) => void;
  onEdit: (item: PortfolioTransaction) => void;
}) {
  if (!props.items.length) {
    return <EmptyStatePanel title="还没有交易记录" description="你可以先录入一笔买入或卖出交易，后续系统会据此生成持仓与收益概览。" />;
  }

  return (
    <div className="glass-panel max-h-[620px] overflow-auto overscroll-contain rounded-[22px]">
      <table className="min-w-[980px] text-sm">
        <thead className="sticky top-0 z-10 bg-[rgba(255,255,255,0.8)] text-[var(--color-text-soft)] backdrop-blur-[14px]">
          <tr>
            {["日期", "股票", "方向", "价格", "股数", "成交额", "手续费", "备注", "操作"].map((label) => (
              <th key={label} className="whitespace-nowrap px-4 py-3 text-left font-medium">{label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(216,236,242,0.8)] text-[var(--color-text)]">
          {props.items.map((item) => (
            <tr key={item.id}>
              <td className="whitespace-nowrap px-4 py-3">{item.trade_date}</td>
              <td className="px-4 py-3">
                <div className="font-medium text-[var(--color-text-strong)]">{item.stock_name}</div>
                <div className="mt-1 text-xs text-[var(--color-text-soft)]">{item.symbol}</div>
              </td>
              <td className={`whitespace-nowrap px-4 py-3 font-medium ${item.trade_type === "buy" ? "text-[var(--color-profit)]" : "text-[var(--color-risk)]"}`}>
                {item.trade_type === "buy" ? "买入" : "卖出"}
              </td>
              <td className="whitespace-nowrap px-4 py-3">{money(item.price)}</td>
              <td className="whitespace-nowrap px-4 py-3">{item.quantity.toLocaleString("zh-CN")}</td>
              <td className="whitespace-nowrap px-4 py-3">{money(item.amount)}</td>
              <td className="whitespace-nowrap px-4 py-3">{money(item.fee)}</td>
              <td className="max-w-[220px] px-4 py-3 text-[var(--color-text-muted)]">{item.note || "--"}</td>
              <td className="whitespace-nowrap px-4 py-3">
                <div className="flex items-center gap-2">
                  <AppButton variant="ghost" onClick={() => props.onEdit(item)} disabled={props.deletingId === item.id}>
                    {props.editingId === item.id ? "编辑中" : "编辑"}
                  </AppButton>
                  <AppButton variant="ghost" onClick={() => props.onDelete(item.id)} disabled={props.deletingId === item.id}>
                    {props.deletingId === item.id ? "删除中..." : "删除"}
                  </AppButton>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PerformancePanel(props: { curve: PortfolioPerformancePoint[]; allocation: PortfolioAllocationItem[] }) {
  if (!props.curve.length) {
    return <EmptyStatePanel title="收益分析将在持仓生成后显示" description="当你至少录入一笔买入交易后，这里会展示账户曲线、仓位占比和阶段表现。" />;
  }

  const latestPoint = props.curve[props.curve.length - 1];
  const allocationRows = props.allocation.filter((item) => (item.market_value ?? 0) > 0);
  const isFlat = allocationRows.length === 0 && latestPoint.market_value === 0 && latestPoint.holding_cost === 0;
  const isNetCashReturned = !isFlat && latestPoint.net_invested < 0;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 xl:grid-cols-4">
        {[
          { label: isFlat ? "当前市值" : "最新市值", value: money(latestPoint.market_value), hint: isFlat ? "当前已清仓，因此市值为 0" : "账户当前总市值" },
          {
            label: isFlat ? "已实现盈亏" : "最新浮盈",
            value: money(isFlat ? latestPoint.realized_pnl : latestPoint.unrealized_pnl),
            hint: isFlat ? "卖出后累计实现的盈亏" : percent(latestPoint.unrealized_pnl_pct),
          },
          {
            label: isFlat ? "累计回笼资金" : isNetCashReturned ? "累计净回笼" : "累计净投入",
            value: money(isFlat ? latestPoint.cash_returned : isNetCashReturned ? Math.abs(latestPoint.net_invested) : latestPoint.net_invested),
            hint: isFlat ? "全部卖出后累计收回的资金" : isNetCashReturned ? "累计卖出已超过累计买入，当前持仓相当于利润仓" : "买入 + 手续费 - 卖出",
          },
          { label: isFlat ? "当前持仓成本" : "当前持仓成本", value: money(latestPoint.holding_cost), hint: isFlat ? "当前已无持仓，因此成本为 0" : "仍在持有仓位的成本" },
        ].map((item) => (
          <div key={item.label} className="data-card rounded-[24px] px-5 py-4">
            <p className="text-sm text-[var(--color-text-soft)]">{item.label}</p>
            <p className="mt-3 break-all text-[1.8rem] font-semibold leading-tight text-[var(--color-text-strong)]">{item.value}</p>
            <p className="mt-2 text-sm text-[var(--color-text-muted)]">{item.hint}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.8fr)]">
        <div className="content-card rounded-[24px] p-4">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-soft)]">收益分析</p>
            <h4 className="mt-2 text-xl font-semibold text-[var(--color-text-strong)]">账户曲线</h4>
          </div>
          <Plot
            className="w-full"
            data={[
              {
                type: "scatter",
                mode: "lines",
                x: props.curve.map((item) => item.date),
                y: props.curve.map((item) =>
                  isFlat ? item.cash_returned : item.net_invested < 0 ? Math.abs(item.net_invested) : item.net_invested,
                ),
                name: isFlat ? "回笼资金" : isNetCashReturned ? "净回笼" : "净投入",
                line: { color: "#6f879b", width: 2 },
              },
              {
                type: "scatter",
                mode: "lines",
                x: props.curve.map((item) => item.date),
                y: props.curve.map((item) => item.market_value),
                name: "当前市值",
                line: { color: "#22c1dc", width: 3 },
                fill: "tozeroy",
                fillcolor: "rgba(34,193,220,0.14)",
              },
              {
                type: "scatter",
                mode: "lines",
                x: props.curve.map((item) => item.date),
                y: props.curve.map((item) => (isFlat ? item.realized_pnl : item.holding_cost)),
                name: isFlat ? "已实现盈亏" : "持仓成本",
                line: { color: "#35d0b5", width: 2, dash: "dash" },
              },
            ] as any}
            layout={{
              autosize: true,
              height: 340,
              paper_bgcolor: "rgba(255,255,255,0)",
              plot_bgcolor: "rgba(255,255,255,0)",
              margin: { l: 48, r: 24, t: 16, b: 32 },
              hovermode: "x unified",
              font: { color: "#1f3a5a" },
              xaxis: { tickfont: { color: "#6f879b" }, gridcolor: "rgba(216,236,242,0.8)", zerolinecolor: "rgba(216,236,242,0.8)" },
              yaxis: { tickfont: { color: "#6f879b" }, gridcolor: "rgba(216,236,242,0.8)", zerolinecolor: "rgba(216,236,242,0.8)" },
              legend: { orientation: "h", y: 1.12 },
            }}
            config={{ displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] }}
            useResizeHandler
          />
        </div>

        <div className="content-card rounded-[24px] p-4">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-soft)]">收益分析</p>
            <h4 className="mt-2 text-xl font-semibold text-[var(--color-text-strong)]">仓位占比</h4>
          </div>
          {allocationRows.length ? (
            <Plot
              className="w-full"
              data={[
                {
                  type: "pie",
                  labels: allocationRows.map((item) => item.stock_name),
                  values: allocationRows.map((item) => item.market_value),
                  textinfo: "label+percent",
                  hole: 0.45,
                  marker: { colors: ["#22c1dc", "#35d0b5", "#7be3d2", "#f06b74", "#5e9fca"] },
                },
              ] as any}
              layout={{
                autosize: true,
                height: 340,
                paper_bgcolor: "rgba(255,255,255,0)",
                plot_bgcolor: "rgba(255,255,255,0)",
                margin: { l: 16, r: 16, t: 16, b: 16 },
                font: { color: "#1f3a5a" },
                showlegend: false,
              }}
              config={{ displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] }}
              useResizeHandler
            />
          ) : (
            <EmptyStatePanel title="当前还没有可分配仓位" description="当持仓形成后，这里会展示各股票的市值占比。" />
          )}
        </div>
      </div>

      <div className="content-card rounded-[24px] p-4">
        <div className="mb-4">
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-text-soft)]">收益分析</p>
          <h4 className="mt-2 text-xl font-semibold text-[var(--color-text-strong)]">持仓表现拆解</h4>
        </div>
        {allocationRows.length ? (
          <div className="glass-panel max-h-[520px] overflow-auto overscroll-contain rounded-[18px]">
            <table className="min-w-[760px] text-sm">
              <thead className="sticky top-0 z-10 bg-[rgba(255,255,255,0.8)] text-[var(--color-text-soft)] backdrop-blur-[14px]">
                <tr>
                  {["股票", "当前市值", "仓位占比", "浮动盈亏"].map((label) => (
                    <th key={label} className="whitespace-nowrap px-4 py-3 text-left font-medium">{label}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[rgba(216,236,242,0.8)] text-[var(--color-text)]">
                {allocationRows.map((item) => (
                  <tr key={item.symbol}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-[var(--color-text-strong)]">{item.stock_name}</div>
                      <div className="mt-1 text-xs text-[var(--color-text-soft)]">{item.symbol}</div>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">{money(item.market_value)}</td>
                    <td className="whitespace-nowrap px-4 py-3">{percent(item.weight_pct)}</td>
                    <td className={`whitespace-nowrap px-4 py-3 ${(item.unrealized_pnl ?? 0) >= 0 ? "text-[var(--color-profit)]" : "text-[var(--color-risk)]"}`}>{money(item.unrealized_pnl)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyStatePanel title="当前还没有持仓表现可拆解" description="录入交易后，系统会在这里显示每只股票的市值占比和浮动表现。" />
        )}
      </div>
    </div>
  );
}

export function PortfolioPage({ currentUser }: PortfolioPageProps) {
  const [activeTab, setActiveTab] = useState<PortfolioSubTab>("summary");
  const [summary, setSummary] = useState<PortfolioSummary>(EMPTY_SUMMARY);
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [transactions, setTransactions] = useState<PortfolioTransaction[]>([]);
  const [curve, setCurve] = useState<PortfolioPerformancePoint[]>([]);
  const [allocation, setAllocation] = useState<PortfolioAllocationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [editingTransactionId, setEditingTransactionId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [passwordStatus, setPasswordStatus] = useState("");
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [formState, setFormState] = useState({
    symbol: "",
    tradeType: "buy" as "buy" | "sell",
    tradeDate: new Date().toISOString().slice(0, 10),
    price: "",
    quantity: "",
    fee: "",
    note: "",
  });

  function resetForm() {
    setEditingTransactionId(null);
    setShowAdvanced(false);
    setFormState({
      symbol: "",
      tradeType: "buy",
      tradeDate: new Date().toISOString().slice(0, 10),
      price: "",
      quantity: "",
      fee: "",
      note: "",
    });
  }

  const isFlat = summary.position_count === 0;
  const isNetCashReturned = !isFlat && summary.net_invested < 0;
  const availableOverview = useMemo(
    () => [
      {
        label: isFlat ? "累计回笼资金" : isNetCashReturned ? "累计净回笼" : "净投入",
        value: money(isFlat ? summary.cash_returned : isNetCashReturned ? Math.abs(summary.net_invested) : summary.net_invested),
        hint: isFlat ? "全部卖出后累计回收资金" : isNetCashReturned ? "累计卖出已超过累计买入，当前持仓相当于利润仓" : "累计买入 + 手续费 - 累计卖出",
      },
      {
        label: "当前市值",
        value: money(summary.market_value),
        hint: `${summary.position_count} 只持仓股票`,
      },
      {
        label: isFlat ? "已实现盈亏" : "浮动盈亏",
        value: money(isFlat ? summary.realized_pnl : summary.unrealized_pnl),
        hint: isFlat ? "当前已无持仓，展示累计已实现结果" : percent(summary.unrealized_pnl_pct),
      },
      { label: "交易笔数", value: String(summary.transaction_count), hint: "个人投资记录总数" },
    ],
    [isFlat, isNetCashReturned, summary],
  );

  async function loadPortfolio() {
    if (!currentUser) return;
    setLoading(true);
    setError("");
    try {
      const [nextSummary, nextPositions, nextTransactions, nextPerformance] = await Promise.all([
        getPortfolioSummary(),
        getPortfolioPositions(),
        getPortfolioTransactions(),
        getPortfolioPerformance(),
      ]);
      setSummary(nextSummary);
      setPositions(nextPositions);
      setTransactions(nextTransactions);
      setCurve(nextPerformance.curve);
      setAllocation(nextPerformance.allocation);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "个人投资数据加载失败。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPortfolio();
  }, [currentUser]);

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError("");
    setPasswordStatus("");

    if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
      setPasswordError("请完整填写当前密码、新密码和确认密码。");
      return;
    }
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError("两次输入的新密码不一致。");
      return;
    }
    if (passwordForm.newPassword.length < 6 || passwordForm.newPassword.length > 20) {
      setPasswordError("新密码长度需为 6-20 位。");
      return;
    }

    try {
      setPasswordSaving(true);
      const result = await changePassword(passwordForm.oldPassword, passwordForm.newPassword);
      setPasswordStatus(result.message || "密码修改成功。");
      setPasswordForm({
        oldPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (nextError) {
      setPasswordError(nextError instanceof Error ? nextError.message : "密码修改失败。");
    } finally {
      setPasswordSaving(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setStatus("");

    if (!formState.symbol.trim() || !formState.price.trim() || !formState.quantity.trim()) {
      setError("请至少填写股票代码、成交价格和股数。");
      return;
    }

      try {
      setSaving(true);
      const payload = {
        symbol: formState.symbol.trim(),
        trade_type: formState.tradeType,
        trade_date: formState.tradeDate,
        price: Number(formState.price),
        quantity: Number(formState.quantity),
        fee: Number(formState.fee || 0),
        note: formState.note.trim() || undefined,
      };
      if (editingTransactionId != null) {
        await updatePortfolioTransaction(editingTransactionId, payload);
        setStatus("交易记录已更新。");
      } else {
        await createPortfolioTransaction(payload);
        setStatus("交易记录已保存。");
      }
      resetForm();
      await loadPortfolio();
      setActiveTab("transactions");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : editingTransactionId != null ? "交易记录更新失败。" : "交易记录保存失败。");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(transactionId: number) {
    try {
      setDeletingId(transactionId);
      setError("");
      await deletePortfolioTransaction(transactionId);
      if (editingTransactionId === transactionId) {
        resetForm();
      }
      setStatus("交易记录已删除。");
      await loadPortfolio();
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "删除交易记录失败。");
    } finally {
      setDeletingId(null);
    }
  }

  function handleEdit(item: PortfolioTransaction) {
    setActiveTab("transactions");
    setEditingTransactionId(item.id);
    setShowAdvanced(Boolean(item.fee) || Boolean(item.note));
    setFormState({
      symbol: item.symbol,
      tradeType: item.trade_type,
      tradeDate: item.trade_date,
      price: String(item.price),
      quantity: String(item.quantity),
      fee: item.fee ? String(item.fee) : "",
      note: item.note ?? "",
    });
    setStatus(`正在编辑 ${item.stock_name} 的交易记录。`);
    setError("");
  }

  return (
    <div className="space-y-4">
      <section className="glass-panel rounded-[28px] p-4">
        <div className="flex flex-wrap gap-2">
          {SUB_TABS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setActiveTab(item.key)}
              className={`inline-flex items-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium transition ${
                activeTab === item.key
                  ? "selected-chip"
                  : "glass-chip text-[var(--color-text-muted)] hover:bg-white/85"
              }`}
            >
              <span>{item.label}</span>
              <span className={`text-xs ${activeTab === item.key ? "text-[var(--color-primary)]" : "text-[var(--color-text-soft)]"}`}>{item.short}</span>
            </button>
          ))}
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-[rgba(240,107,116,0.22)] bg-[rgba(240,107,116,0.1)] px-4 py-3 text-sm text-[var(--color-danger)]">{error}</div> : null}
      {status ? <div className="glass-panel rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)]">{status}</div> : null}

      {activeTab === "summary" ? (
        <div className="space-y-4">
          <SectionShell
            eyebrow="个人投资"
            title="账户概览"
            description="从交易记录中汇总净投入、当前市值和浮动盈亏。当前阶段先把记账、持仓和概览跑通，再逐步补齐更细的收益分析。"
            actions={<AppButton onClick={() => setActiveTab("transactions")}>去录入交易</AppButton>}
          >
            {loading ? <p className="text-sm text-[var(--color-text-muted)]">正在加载账户概览...</p> : <SummaryCards summary={summary} />}
          </SectionShell>

          <SectionShell
            eyebrow="个人投资"
            title="关键概览"
            description="这一组卡片用来快速判断当前账户的投入状态、持仓规模和收益表现。"
          >
            <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
              {availableOverview.map((item) => (
                <div key={item.label} className="data-card rounded-[24px] px-5 py-4">
                  <p className="text-sm text-[var(--color-text-soft)]">{item.label}</p>
                  <p className="mt-3 break-all text-[1.75rem] font-semibold leading-tight text-[var(--color-text-strong)] xl:text-[2rem]">{item.value}</p>
                  <p className="mt-2 text-sm text-[var(--color-text-muted)]">{item.hint}</p>
                </div>
              ))}
            </div>
          </SectionShell>

          <SectionShell
            eyebrow="账户安全"
            title="修改登录密码"
            description="已登录后可在这里完成基础版修改密码。需要先验证当前密码，再设置新的登录密码。"
          >
            <form className="grid gap-4 xl:grid-cols-3" onSubmit={handlePasswordSubmit}>
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">当前密码</span>
                <input
                  type="password"
                  value={passwordForm.oldPassword}
                  maxLength={32}
                  onChange={(event) => setPasswordForm((current) => ({ ...current, oldPassword: event.target.value }))}
                  className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                  placeholder="请输入当前密码"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">新密码</span>
                <input
                  type="password"
                  value={passwordForm.newPassword}
                  maxLength={32}
                  onChange={(event) => setPasswordForm((current) => ({ ...current, newPassword: event.target.value }))}
                  className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                  placeholder="6-20 位即可"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">确认新密码</span>
                <input
                  type="password"
                  value={passwordForm.confirmPassword}
                  maxLength={32}
                  onChange={(event) => setPasswordForm((current) => ({ ...current, confirmPassword: event.target.value }))}
                  className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                  placeholder="请再次输入新密码"
                />
              </label>
              <div className="xl:col-span-full flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm text-[var(--color-text-muted)]">新密码长度 6-20 位，不额外限制字符类型。</div>
                <AppButton type="submit" disabled={passwordSaving}>
                  {passwordSaving ? "正在修改..." : "确认修改密码"}
                </AppButton>
              </div>
              {passwordError ? <p className="xl:col-span-full text-sm text-[var(--color-danger)]">{passwordError}</p> : null}
              {passwordStatus ? <p className="xl:col-span-full text-sm text-[var(--color-text-strong)]">{passwordStatus}</p> : null}
            </form>
          </SectionShell>
        </div>
      ) : null}

      {activeTab === "positions" ? (
        <SectionShell
          eyebrow="个人投资"
          title="当前持仓"
          description="基于你的买入卖出流水，系统会按 A 股价格与股数计算当前持仓、成本和浮动盈亏。"
        >
          {loading ? <p className="text-sm text-[var(--color-text-muted)]">正在加载持仓数据...</p> : <PositionsTable items={positions} />}
        </SectionShell>
      ) : null}

      {activeTab === "transactions" ? (
        <div className="space-y-4">
          <SectionShell
            eyebrow="个人投资"
            title={editingTransactionId != null ? "编辑交易记录" : "新增交易记录"}
            description="第一版采用简化录入：股票代码、买卖方向、交易日期、成交价格和股数是必填，手续费和备注先放到可选高级项里。"
            actions={editingTransactionId != null ? <AppButton variant="ghost" onClick={resetForm}>取消编辑</AppButton> : undefined}
          >
            <form className="grid gap-4 xl:grid-cols-[repeat(5,minmax(0,1fr))] 2xl:grid-cols-[repeat(6,minmax(0,1fr))]" onSubmit={handleSubmit}>
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">股票代码</span>
                <input
                  value={formState.symbol}
                  onChange={(event) => setFormState((current) => ({ ...current, symbol: event.target.value }))}
                  className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                  placeholder="例如 002594"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">买卖方向</span>
                <select
                  value={formState.tradeType}
                  onChange={(event) => setFormState((current) => ({ ...current, tradeType: event.target.value as "buy" | "sell" }))}
                  className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                >
                  <option value="buy">买入</option>
                  <option value="sell">卖出</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">交易日期</span>
                <input
                  type="date"
                  value={formState.tradeDate}
                  onChange={(event) => setFormState((current) => ({ ...current, tradeDate: event.target.value }))}
                  className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">成交价格</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formState.price}
                  onChange={(event) => setFormState((current) => ({ ...current, price: event.target.value }))}
                  className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                  placeholder="例如 234.50"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">股数</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={formState.quantity}
                  onChange={(event) => setFormState((current) => ({ ...current, quantity: event.target.value }))}
                  className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                  placeholder="例如 100"
                />
              </label>
              <div className="xl:col-span-full">
                <button type="button" onClick={() => setShowAdvanced((current) => !current)} className="text-sm font-medium text-[var(--color-primary)]">
                  {showAdvanced ? "收起高级设置" : "展开高级设置"}
                </button>
              </div>
              {showAdvanced ? (
                <>
                  <label className="block xl:col-span-1">
                    <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">手续费</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={formState.fee}
                      onChange={(event) => setFormState((current) => ({ ...current, fee: event.target.value }))}
                      className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                      placeholder="默认 0"
                    />
                  </label>
                  <label className="block xl:col-span-3 2xl:col-span-4">
                    <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[var(--color-text-soft)]">备注</span>
                    <input
                      value={formState.note}
                      onChange={(event) => setFormState((current) => ({ ...current, note: event.target.value }))}
                      className="glass-chip w-full rounded-2xl px-4 py-3 text-sm text-[var(--color-text-strong)] outline-none transition focus:border-[color:var(--color-primary-border)] focus:bg-white/85"
                      placeholder="例如 分批建仓、调仓减仓"
                    />
                  </label>
                </>
              ) : null}
              <div className="xl:col-span-full flex justify-end">
                <AppButton type="submit" disabled={saving}>
                  {saving ? "保存中..." : editingTransactionId != null ? "保存修改" : "保存交易记录"}
                </AppButton>
              </div>
            </form>
          </SectionShell>

          <SectionShell
            eyebrow="个人投资"
            title="交易流水"
            description="你录入的买入卖出记录会在这里展示，并作为持仓和账户概览的计算基础。"
          >
            {loading ? (
              <p className="text-sm text-[var(--color-text-muted)]">正在加载交易记录...</p>
            ) : (
              <TransactionsTable
                items={transactions}
                deletingId={deletingId}
                editingId={editingTransactionId}
                onDelete={(id) => void handleDelete(id)}
                onEdit={handleEdit}
              />
            )}
          </SectionShell>
        </div>
      ) : null}

      {activeTab === "performance" ? (
        <SectionShell
          eyebrow="个人投资"
          title="收益分析"
          description="这里会集中展示账户曲线、仓位占比和当前持仓表现。后续还可以在这一页继续补组合净值、阶段回撤和收益归因。"
        >
          {loading ? <p className="text-sm text-[var(--color-text-muted)]">正在加载收益分析...</p> : <PerformancePanel curve={curve} allocation={allocation} />}
        </SectionShell>
      ) : null}
    </div>
  );
}
