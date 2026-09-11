import { useCallback } from "react";
import { useAsync } from "../hooks/useAsync";
import { getInsights } from "../api/endpoints";
import type { Insight, InsightCategory } from "../types/api";
import { formatDateTime } from "../lib/format";
import { LoadingState, ErrorState } from "../components/LoadingState";

const CATEGORY_ORDER: InsightCategory[] = ["spending", "budget", "savings", "portfolio"];
const CATEGORY_LABEL: Record<InsightCategory, string> = {
  spending: "Spending",
  budget: "Budget",
  savings: "Savings",
  portfolio: "Portfolio",
};

function groupByCategory(insights: Insight[]): Map<InsightCategory, Insight[]> {
  const map = new Map<InsightCategory, Insight[]>();
  for (const insight of insights) {
    const list = map.get(insight.category) ?? [];
    list.push(insight);
    map.set(insight.category, list);
  }
  for (const list of map.values()) {
    list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }
  return map;
}

export default function Insights() {
  const { data, loading, error } = useAsync(useCallback(() => getInsights(), []), []);

  const grouped = data ? groupByCategory(data) : new Map<InsightCategory, Insight[]>();

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Insights</h1>
          <div className="page-subtitle">
            Rule-based observations across spending, budgets, savings, and portfolio
            activity — regenerated each time this page loads
          </div>
        </div>
      </div>

      {loading && <LoadingState label="Generating insights…" />}
      {error && <ErrorState message={error} />}

      {data && data.length === 0 && (
        <div className="card">
          <p className="muted">
            No insights yet. Add some transactions, budgets, or portfolio activity
            to generate insights.
          </p>
        </div>
      )}

      {data &&
        data.length > 0 &&
        CATEGORY_ORDER.filter((cat) => grouped.has(cat)).map((cat) => (
          <div className="card" key={cat}>
            <div className="card-header">
              <h2>{CATEGORY_LABEL[cat]}</h2>
              <span className="card-header-sub">{grouped.get(cat)!.length} insight(s)</span>
            </div>
            {grouped.get(cat)!.map((insight) => (
              <div className="insight-item" key={insight.id}>
                <div>
                  <div className="insight-body">{insight.message}</div>
                  <div className="insight-time">{formatDateTime(insight.created_at)}</div>
                </div>
              </div>
            ))}
          </div>
        ))}
    </div>
  );
}
