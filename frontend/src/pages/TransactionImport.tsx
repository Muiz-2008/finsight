import { useCallback, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useAsync } from "../hooks/useAsync";
import { importTransactions, listAccounts } from "../api/endpoints";
import type { ImportReport } from "../types/api";
import { ApiError } from "../api/client";
import { LoadingState, ErrorState } from "../components/LoadingState";

export default function TransactionImport() {
  const { data: accounts, loading, error } = useAsync(
    useCallback(() => listAccounts(), []),
    [],
  );
  const [accountId, setAccountId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    setReport(null);
    if (!accountId || !file) {
      setSubmitError("Choose an account and a CSV file.");
      return;
    }
    setSubmitting(true);
    try {
      const result = await importTransactions(accountId, file);
      setReport(result);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.detail : "Import failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Import transactions</h1>
          <div className="page-subtitle">
            Upload a CSV with columns: date, description, amount, category, type
          </div>
        </div>
      </div>

      {loading && <LoadingState label="Loading accounts…" />}
      {error && <ErrorState message={error} />}

      {accounts && (
        <div className="card" style={{ maxWidth: 520 }}>
          {submitError && <div className="callout callout-error">{submitError}</div>}
          {accounts.length === 0 && (
            <div className="callout callout-warning">
              You need at least one account before importing. Create one from the
              Portfolio or Transactions page first.
            </div>
          )}
          <form onSubmit={handleSubmit}>
            <div className="form-grid" style={{ gridTemplateColumns: "1fr" }}>
              <div className="field">
                <label>Account</label>
                <select
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  required
                >
                  <option value="">Select…</option>
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>CSV file</label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  required
                />
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Importing…" : "Import"}
              </button>
            </div>
          </form>
        </div>
      )}

      {report && (
        <div className="card" style={{ maxWidth: 520 }}>
          <div className="card-header">
            <h2>Import report</h2>
          </div>
          <div className="stat-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
            <div className="stat-tile">
              <div className="stat-label">Total rows</div>
              <div className="stat-value">{report.total_rows}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Imported</div>
              <div className="stat-value positive">{report.imported}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Duplicates</div>
              <div className="stat-value">{report.duplicates}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Invalid</div>
              <div className={`stat-value ${report.invalid > 0 ? "negative" : ""}`}>
                {report.invalid}
              </div>
            </div>
          </div>
          {report.errors.length > 0 && (
            <>
              <h3 style={{ marginTop: 16 }}>Errors</h3>
              <ul style={{ fontSize: 12.5, color: "var(--text-secondary)", paddingLeft: 18 }}>
                {report.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
