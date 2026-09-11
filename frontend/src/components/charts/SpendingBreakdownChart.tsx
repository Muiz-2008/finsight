import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SpendingByCategory } from "../../types/api";
import { formatCurrency, formatPercent } from "../../lib/format";
import { COLOR_AXIS, COLOR_GRID } from "../../lib/colors";

// Single-hue sequential ramp (blue), lightest -> darkest, for ranking
// categories by magnitude. Identity is already carried by the axis label.
const RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#184f95", "#104281"];

interface TooltipPayloadItem {
  payload: { category: string; total: number; percentage_of_spending: number };
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="card" style={{ margin: 0, padding: "8px 12px" }}>
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{row.category}</div>
      <div style={{ fontSize: 12 }}>
        {formatCurrency(row.total)} · {formatPercent(row.percentage_of_spending / 100)}
      </div>
    </div>
  );
}

export function SpendingBreakdownChart({ data }: { data: SpendingByCategory[] }) {
  const rows = [...data]
    .map((d) => ({ ...d, total: Number(d.total) }))
    .sort((a, b) => b.total - a.total);

  if (rows.length === 0) {
    return <div className="loading-state">No spending in this period.</div>;
  }

  const height = Math.max(180, rows.length * 30);

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 4, right: 24, left: 0, bottom: 0 }}
        >
          <CartesianGrid stroke={COLOR_GRID} horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: COLOR_AXIS }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) =>
              new Intl.NumberFormat("en-US", {
                notation: "compact",
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0,
              }).format(v)
            }
          />
          <YAxis
            type="category"
            dataKey="category"
            tick={{ fontSize: 12, fill: "var(--text-primary)" }}
            axisLine={false}
            tickLine={false}
            width={100}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(0,0,0,0.03)" }} />
          <Bar dataKey="total" radius={[0, 3, 3, 0]} maxBarSize={18}>
            {rows.map((row, i) => (
              <Cell key={row.category} fill={RAMP[Math.min(i, RAMP.length - 1)]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
