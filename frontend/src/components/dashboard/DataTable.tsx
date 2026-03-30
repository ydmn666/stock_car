import type { StockRecord } from "../../types";

type DataTableProps = {
  records: StockRecord[];
};

export function DataTable({ records }: DataTableProps) {
  const rows = [...records].reverse();
  if (!rows.length) return null;
  const keys = Object.keys(rows[0]);

  return (
    <div className="max-h-[560px] overflow-auto overscroll-contain rounded-[22px] border border-white/8 bg-[#0f172a]">
      <table className="min-w-[1080px] text-sm">
        <thead className="sticky top-0 z-10 bg-[#111827] text-slate-400">
          <tr>
            {keys.map((key) => (
              <th key={key} className="whitespace-nowrap px-4 py-3 text-left font-medium">{key}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/6 text-slate-200">
          {rows.map((record, index) => (
            <tr key={index}>
              {keys.map((key) => (
                <td key={key} className="whitespace-nowrap px-4 py-3">{String(record[key] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
