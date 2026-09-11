import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MonthlyCashflow } from "../../types/api";
import { formatCurrency } from "../../lib/format";
import { COLOR_AXIS, COLOR_GRID, SERIES_COLORS } from "../../lib/colors";

function monthLabel(month: string): string {
  const d = new Date(`${month}-01T00:00:00`);
  if (Number.isNaN(d.getTime())) return month;
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

interface TooltipPayloadItem {
  dataKey: string;
  value: number;
  color: string;
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const names: Record<string, string> = {
    income: "Income",
    expenses: "Expenses",
    net: "Net",
  };
  return (
    <div className="card" style={{ margin: 0, padding: "8px 12px" }}>
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
        {monthLabel(label ?? "")}
      </div>
      {payload.map((p) => (
        <div
          key={p.dataKey}
          style={{ fontSize: 12, display: "flex", justifyContent: "space-between", gap: 16 }}
        >
          <span style={{ color: p.color }}>{names[p.dataKey] ?? p.dataKey}</span>
          <span className="mono">{formatCurrency(p.value)}</span>
        </div>
      ))}
    </div>
  );
}

export function CashflowMonthlyChart({ data }: { data: MonthlyCashflow[] }) {
  const rows = data.map((d) => ({
    month: d.month,
    income: Number(d.income),
    expenses: Number(d.expenses),
    net: Number(d.net),
  }));

  return (
    <>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={COLOR_GRID} vertical={false} />
            <XAxis
              dataKey="month"
              tickFormatter={monthLabel}
              tick={{ fontSize: 11, fill: COLOR_AXIS }}
              axisLine={{ stroke: COLOR_AXIS }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: COLOR_AXIS }}
              axisLine={false}
              tickLine={false}
              width={56}
              tickFormatter={(v: number) =>
                new Intl.NumberFormat("en-US", {
                  notation: "compact",
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0,
                }).format(v)
              }
            />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(0,0,0,0.03)" }} />
            <Bar dataKey="income" fill={SERIES_COLORS[0]} radius={[3, 3, 0, 0]} maxBarSize={22} />
            <Bar dataKey="expenses" fill={SERIES_COLORS[1]} radius={[3, 3, 0, 0]} maxBarSize={22} />
            <Line
              type="monotone"
              dataKey="net"
              stroke={SERIES_COLORS[6]}
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="legend-row">
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: SERIES_COLORS[0] }} />
          Income
        </span>
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: SERIES_COLORS[1] }} />
          Expenses
        </span>
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: SERIES_COLORS[6] }} />
          Net
        </span>
      </div>
    </>
  );
}
