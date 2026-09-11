import { useCallback, useState } from "react";
import type { FormEvent } from "react";
import { useAsync } from "../hooks/useAsync";
import { getBudgetAnalytics, listCategories, upsertBudget } from "../api/endpoints";
import { ApiError } from "../api/client";
import { formatCurrency, toNum } from "../lib/format";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { BudgetStatusBadge } from "../components/StatusBadge";
import { startOfMonth, today } from "../lib/dates";

export default function Budgets() {
  const [categoryId, setCategoryId] = useState("");
  const [limit, setLimit] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { data: categories } = useAsync(useCallback(() => listCategories(), []), []);

  const loadAnalytics = useCallback(
    () => getBudgetAnalytics(startOfMonth(), today()),
    [],
  );
  const { data: analytics, loading, error, reload } = useAsync(loadAnalytics, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    const limitNum = Number(limit);
    if (!categoryId) {
      setFormError("Select a category.");
      return;
    }
    if (!Number.isFinite(limitNum) || limitNum <= 0) {
      setFormError("Monthly limit must be a positive number.");
      return;
    }
    setSubmitting(true);
    try {
      await upsertBudget(categoryId, limitNum);
      setLimit("");
      reload();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.detail : "Save failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Budgets</h1>
          <div className="page-subtitle">Monthly limits vs. actual spend, this month</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 480 }}>
        <div className="card-header">
          <h2>Set a monthly budget</h2>
        </div>
        {formError && <div className="callout callout-error">{formError}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="field">
              <label>Category</label>
              <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} required>
                <option value="">Select…</option>
                {(categories ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Monthly limit</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
                required
              />
            </div>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Saving…" : "Save budget"}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Budget vs. actual</h2>
        </div>
        {loading && <LoadingState label="Loading budgets…" />}
        {error && <ErrorState message={error} />}
        {analytics && (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th className="num">Budgeted</th>
                  <th className="num">Actual</th>
                  <th className="num">Remaining</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {analytics.length === 0 && (
                  <tr className="empty-row">
                    <td colSpan={5}>No budgets set yet.</td>
                  </tr>
                )}
                {analytics.map((row) => {
                  const remaining = (toNum(row.budgeted) ?? 0) - (toNum(row.actual) ?? 0);
                  return (
                    <tr key={row.category}>
                      <td>{row.category}</td>
                      <td className="num">{formatCurrency(row.budgeted)}</td>
                      <td className="num">{formatCurrency(row.actual)}</td>
                      <td className={`num ${remaining < 0 ? "negative" : ""}`}>
                        {formatCurrency(remaining)}
                      </td>
                      <td>
                        <BudgetStatusBadge status={row.status} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
