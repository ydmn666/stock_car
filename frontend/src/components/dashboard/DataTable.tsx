import type { PriceBar } from "../../types";

type DataTableProps = {
  records: PriceBar[];
};

const COLUMNS: Array<{ key: keyof PriceBar; label: string }> = [
  { key: "trade_date", label: "日期" },
  { key: "open", label: "开盘" },
  { key: "high", label: "最高" },
  { key: "low", label: "最低" },
  { key: "close", label: "收盘" },
  { key: "volume", label: "成交量" },
  { key: "turnover", label: "成交额" },
  { key: "pct_change", label: "涨跌幅" },
  { key: "source", label: "来源" },
];

export function DataTable({ records }: DataTableProps) {
  const rows = [...records].reverse();
  if (!rows.length) return null;

  return (
    <div className="glass-panel max-h-[560px] overflow-auto overscroll-contain rounded-[22px]">
      <table className="min-w-[1080px] text-sm">
        <thead className="sticky top-0 z-10 bg-[rgba(255,255,255,0.8)] text-[var(--color-text-soft)] backdrop-blur-[14px]">
          <tr>
            {COLUMNS.map((column) => (
              <th key={column.key} className="whitespace-nowrap px-4 py-3 text-left font-medium">{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(216,236,242,0.8)] text-[var(--color-text)]">
          {rows.map((record) => (
            <tr key={`${record.instrument_id}:${record.trade_date}`}>
              {COLUMNS.map((column) => (
                <td key={column.key} className="whitespace-nowrap px-4 py-3">{String(record[column.key] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

