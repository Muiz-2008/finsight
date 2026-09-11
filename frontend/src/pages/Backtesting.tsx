import { useState } from "react";
import type { FormEvent } from "react";
import { runBacktest } from "../api/endpoints";
import type { BacktestResult } from "../types/api";
import { ApiError } from "../api/client";
import { formatCurrency, formatNumber, formatPercent, signClass } from "../lib/format";
import { daysAgo, today } from "../lib/dates";
import { EquityCurveChart } from "../components/charts/EquityCurveChart";

interface FormState {
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: string;
  short_window: string;
  long_window: string;
  transaction_cost_bps: string;
}

function defaultForm(): FormState {
  return {
    symbol: "AAPL",
    start_date: daysAgo(365),
    end_date: today(),
    initial_capital: "10000",
    short_window: "20",
    long_window: "50",
    transaction_cost_bps: "10",
  };
}

export default function Backtesting() {
  const [form, setForm] = useState<FormState>(defaultForm());
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BacktestResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    const shortWindow = Number(form.short_window);
    const longWindow = Number(form.long_window);
    if (shortWindow >= longWindow) {
      setError("Short window must be smaller than long window.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await runBacktest({
        symbol: form.symbol.trim().toUpperCase(),
        start_date: form.start_date,
        end_date: form.end_date,
        initial_capital: Number(form.initial_capital) || undefined,
        short_window: shortWindow || undefined,
        long_window: longWindow || undefined,
        transaction_cost_bps: Number(form.transaction_cost_bps) || undefined,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Backtest failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Backtesting</h1>
          <div className="page-subtitle">Moving-average crossover strategy simulator</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 680 }}>
        {error && <div className="callout callout-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="field">
              <label>Symbol</label>
              <input
                type="text"
                value={form.symbol}
                onChange={(e) => setForm((f) => ({ ...f, symbol: e.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label>Start date</label>
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label>End date</label>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label>Initial capital</label>
              <input
                type="number"
                min="1"
                step="100"
                value={form.initial_capital}
                onChange={(e) => setForm((f) => ({ ...f, initial_capital: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>Short window (days)</label>
              <input
                type="number"
                min="1"
                value={form.short_window}
                onChange={(e) => setForm((f) => ({ ...f, short_window: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>Long window (days)</label>
              <input
                type="number"
                min="2"
                value={form.long_window}
                onChange={(e) => setForm((f) => ({ ...f, long_window: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>Transaction cost (bps)</label>
              <input
                type="number"
                min="0"
                value={form.transaction_cost_bps}
                onChange={(e) =>
                  setForm((f) => ({ ...f, transaction_cost_bps: e.target.value }))
                }
              />
            </div>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Running backtest…" : "Run backtest"}
            </button>
          </div>
        </form>
      </div>

      {result && (
        <div className="card">
          <div className="callout callout-disclaimer">{result.disclaimer}</div>

          <div className="card-header">
            <h2>
              {result.symbol} · {result.strategy}
            </h2>
            <span className="card-header-sub">
              {result.start_date} – {result.end_date}
            </span>
          </div>

          <div className="stat-grid" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            <div className="stat-tile">
              <div className="stat-label">Final value</div>
              <div className="stat-value">{formatCurrency(result.final_value)}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Total return</div>
              <div className={`stat-value ${signClass(result.total_return)}`}>
                {formatPercent(result.total_return)}
              </div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Annualized return</div>
              <div className={`stat-value ${signClass(result.annualized_return)}`}>
                {formatPercent(result.annualized_return)}
              </div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Annualized volatility</div>
              <div className="stat-value">{formatPercent(result.annualized_volatility)}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Sharpe ratio</div>
              <div className="stat-value">{formatNumber(result.sharpe_ratio)}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Max drawdown</div>
              <div className="stat-value negative">{formatPercent(result.max_drawdown)}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Number of trades</div>
              <div className="stat-value">{result.num_trades}</div>
            </div>
          </div>

          <h3 style={{ marginTop: 16, marginBottom: 8 }}>Equity curve</h3>
          <EquityCurveChart equityCurve={result.equity_curve} />
        </div>
      )}
    </div>
  );
}
