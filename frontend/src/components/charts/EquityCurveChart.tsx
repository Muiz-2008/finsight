import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrency } from "../../lib/format";
import { COLOR_AXIS, COLOR_GRID, SERIES_COLORS } from "../../lib/colors";

interface TooltipPayloadItem {
  value: number;
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: number;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="card" style={{ margin: 0, padding: "8px 12px" }}>
      <div style={{ fontSize: 12, marginBottom: 2 }}>Day {label}</div>
      <div style={{ fontSize: 12, fontWeight: 600 }}>{formatCurrency(payload[0].value)}</div>
    </div>
  );
}

export function EquityCurveChart({ equityCurve }: { equityCurve: number[] }) {
  const rows = equityCurve.map((value, i) => ({ day: i, value }));

  return (
    <div className="chart-wrap" style={{ height: 300 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={SERIES_COLORS[0]} stopOpacity={0.22} />
              <stop offset="100%" stopColor={SERIES_COLORS[0]} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={COLOR_GRID} vertical={false} />
          <XAxis
            dataKey="day"
            tick={{ fontSize: 11, fill: COLOR_AXIS }}
            axisLine={{ stroke: COLOR_AXIS }}
            tickLine={false}
            label={{ value: "Trading day", position: "insideBottom", offset: -2, fontSize: 11, fill: COLOR_AXIS }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: COLOR_AXIS }}
            axisLine={false}
            tickLine={false}
            width={64}
            tickFormatter={(v: number) =>
              new Intl.NumberFormat("en-US", {
                notation: "compact",
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0,
              }).format(v)
            }
          />
          <Tooltip content={<ChartTooltip />} />
          <Area
            type="monotone"
            dataKey="value"
            stroke={SERIES_COLORS[0]}
            strokeWidth={2}
            fill="url(#equityFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
