import { useCallback } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "../hooks/useAsync";
import {
  getCashflow,
  getInsights,
  getMonthlyCashflow,
  getPerformance,
  getSpending,
  listPortfolios,
  listTransactions,
} from "../api/endpoints";
import { monthsAgoStart, startOfMonth, today } from "../lib/dates";
import { formatCurrency, formatDate, formatPercent, signClass } from "../lib/format";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { TransactionTypeBadge } from "../components/StatusBadge";
import { CashflowMonthlyChart } from "../components/charts/CashflowMonthlyChart";
import { SpendingBreakdownChart } from "../components/charts/SpendingBreakdownChart";
import type { Insight } from "../types/api";

const INSIGHT_LABEL: Record<Insight["category"], string> = {
  spending: "Spending",
  budget: "Budget",
  savings: "Savings",
  portfolio: "Portfolio",
};

async function loadDashboard() {
  const monthStart = startOfMonth();
  const todayStr = today();

  const [cashflow, monthly, spending, portfolios, recentTx, insights] =
    await Promise.all([
      getCashflow(monthStart, todayStr),
      getMonthlyCashflow(monthsAgoStart(6), todayStr),
      getSpending(monthStart, todayStr),
      listPortfolios(),
      listTransactions({ limit: 8, offset: 0, sort_desc: true }),
      getInsights(),
    ]);

  let totalPortfolioValue = 0;
  if (portfolios.length > 0) {
    const performances = await Promise.all(
      portfolios.map((p) => getPerformance(p.id).catch(() => null)),
    );
    totalPortfolioValue = performances.reduce(
      (sum, perf) => sum + (perf ? Number(perf.total_market_value) : 0),
      0,
    );
  }

  return { cashflow, monthly, spending, totalPortfolioValue, recentTx, insights };
}

export default function Dashboard() {
  const load = useCallback(() => loadDashboard(), []);
  const { data, loading, error } = useAsync(load, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <div className="page-subtitle">
            Overview for {formatDate(startOfMonth())} – {formatDate(today())}
          </div>
        </div>
      </div>

      {loading && <LoadingState label="Loading dashboard…" />}
      {error && <ErrorState message={error} />}

      {data && (
        <>
          <div className="stat-grid">
            <div className="stat-tile">
              <div className="stat-label">Net cashflow (MTD)</div>
              <div className={`stat-value ${signClass(data.cashflow.net_cashflow)}`}>
                {formatCurrency(data.cashflow.net_cashflow)}
              </div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Income (MTD)</div>
              <div className="stat-value">{formatCurrency(data.cashflow.income)}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Expenses (MTD)</div>
              <div className="stat-value">{formatCurrency(data.cashflow.expenses)}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Savings rate (MTD)</div>
              <div className="stat-value">
                {formatPercent(data.cashflow.savings_rate)}
              </div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Total portfolio value</div>
              <div className="stat-value">{formatCurrency(data.totalPortfolioValue)}</div>
            </div>
          </div>

          <div className="dashboard-grid">
            <div>
              <div className="card">
                <div className="card-header">
                  <h2>Cashflow, last 6 months</h2>
                </div>
                <CashflowMonthlyChart data={data.monthly} />
              </div>

              <div className="card">
                <div className="card-header">
                  <h2>Recent transactions</h2>
                  <Link to="/transactions" className="card-header-sub">
                    View all →
                  </Link>
                </div>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Type</th>
                        <th className="num">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recentTx.items.length === 0 && (
                        <tr className="empty-row">
                          <td colSpan={4}>No transactions yet.</td>
                        </tr>
                      )}
                      {data.recentTx.items.map((tx) => (
                        <tr key={tx.id}>
                          <td>{formatDate(tx.date)}</td>
                          <td>{tx.description || <span className="muted">—</span>}</td>
                          <td>
                            <TransactionTypeBadge type={tx.transaction_type} />
                          </td>
                          <td
                            className={`num ${
                              tx.transaction_type === "income" ? "positive" : ""
                            }`}
                          >
                            {tx.transaction_type === "income" ? "+" : "-"}
                            {formatCurrency(tx.amount, tx.currency)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div>
              <div className="card">
                <div className="card-header">
                  <h2>Spending by category</h2>
                </div>
                <SpendingBreakdownChart data={data.spending.by_category} />
              </div>

              <div className="card">
                <div className="card-header">
                  <h2>Latest insights</h2>
                  <Link to="/insights" className="card-header-sub">
                    View all →
                  </Link>
                </div>
                {data.insights.length === 0 && (
                  <p className="muted">No insights yet.</p>
                )}
                {data.insights.slice(0, 5).map((insight) => (
                  <div className="insight-item" key={insight.id}>
                    <span className="badge badge-neutral insight-tag">
                      {INSIGHT_LABEL[insight.category]}
                    </span>
                    <div>
                      <div className="insight-body">{insight.message}</div>
                      <div className="insight-time">{formatDate(insight.created_at)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
