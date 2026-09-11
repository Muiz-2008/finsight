import type { CorrelationMatrix } from "../../types/api";

// Diverging blue <-> red pair with a neutral gray midpoint at 0, matching the
// app's diverging convention. Correlation is bounded [-1, 1] so we interpolate
// directly rather than needing a data-driven domain.
function cellColor(value: number): string {
  const v = Math.max(-1, Math.min(1, value));
  if (v >= 0) {
    // white/neutral -> blue
    const t = v; // 0..1
    const r = Math.round(240 + (0x2a - 240) * t);
    const g = Math.round(239 + (0x78 - 239) * t);
    const b = Math.round(236 + (0xd6 - 236) * t);
    return `rgb(${r},${g},${b})`;
  }
  const t = -v; // 0..1
  const r = Math.round(240 + (0xe3 - 240) * t);
  const g = Math.round(239 + (0x49 - 239) * t);
  const b = Math.round(236 + (0x48 - 236) * t);
  return `rgb(${r},${g},${b})`;
}

function textColor(value: number): string {
  return Math.abs(value) > 0.6 ? "#ffffff" : "var(--text-primary)";
}

export function CorrelationHeatmap({ matrix }: { matrix: CorrelationMatrix }) {
  const symbols = Object.keys(matrix);
  if (symbols.length === 0) {
    return <p className="muted">Not enough data for a correlation matrix.</p>;
  }
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th></th>
            {symbols.map((s) => (
              <th key={s} className="num">
                {s}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {symbols.map((row) => (
            <tr key={row}>
              <th>{row}</th>
              {symbols.map((col) => {
                const v = matrix[row]?.[col];
                const value = typeof v === "number" ? v : NaN;
                return (
                  <td
                    key={col}
                    className="heatmap-cell"
                    style={{
                      background: Number.isFinite(value) ? cellColor(value) : undefined,
                      color: Number.isFinite(value) ? textColor(value) : undefined,
                    }}
                  >
                    {Number.isFinite(value) ? value.toFixed(2) : "N/A"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
