import { useCallback, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useAsync } from "../hooks/useAsync";
import {
  createTransaction,
  deleteTransaction,
  listAccounts,
  listCategories,
  listTransactions,
  updateTransaction,
} from "../api/endpoints";
import type { Account, Category, Transaction, TransactionType } from "../types/api";
import { ApiError } from "../api/client";
import { formatCurrency, formatDate } from "../lib/format";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Pagination } from "../components/Pagination";
import { TransactionTypeBadge } from "../components/StatusBadge";

const PAGE_SIZE = 20;
const EMPTY_ACCOUNTS: Account[] = [];
const EMPTY_CATEGORIES: Category[] = [];

interface Filters {
  date_from: string;
  date_to: string;
  category_id: string;
  account_id: string;
  transaction_type: string;
}

const EMPTY_FILTERS: Filters = {
  date_from: "",
  date_to: "",
  category_id: "",
  account_id: "",
  transaction_type: "",
};

interface FormState {
  id: string | null;
  account_id: string;
  category_id: string;
  amount: string;
  currency: string;
  transaction_type: TransactionType;
  description: string;
  date: string;
}

function blankForm(defaultAccount?: string): FormState {
  return {
    id: null,
    account_id: defaultAccount ?? "",
    category_id: "",
    amount: "",
    currency: "USD",
    transaction_type: "expense",
    description: "",
    date: new Date().toISOString().slice(0, 10),
  };
}

export default function Transactions() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [offset, setOffset] = useState(0);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<FormState>(blankForm());
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadRefs = useAsync(
    useCallback(
      () => Promise.all([listAccounts(), listCategories()]),
      [],
    ),
    [],
  );
  const accounts = loadRefs.data?.[0] ?? EMPTY_ACCOUNTS;
  const categories = loadRefs.data?.[1] ?? EMPTY_CATEGORIES;

  const accountName = useMemo(
    () => new Map(accounts.map((a) => [a.id, a.name])),
    [accounts],
  );
  const categoryName = useMemo(
    () => new Map(categories.map((c) => [c.id, c.name])),
    [categories],
  );

  const loadTx = useCallback(
    () =>
      listTransactions({
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
        category_id: filters.category_id || undefined,
        account_id: filters.account_id || undefined,
        transaction_type: filters.transaction_type || undefined,
        limit: PAGE_SIZE,
        offset,
        sort_desc: true,
      }),
    [filters, offset],
  );
  const { data, loading, error, reload } = useAsync(loadTx, [filters, offset]);

  function updateFilter<K extends keyof Filters>(key: K, value: Filters[K]) {
    setFilters((f) => ({ ...f, [key]: value }));
    setOffset(0);
  }

  function openCreate() {
    setForm(blankForm(accounts[0]?.id));
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(tx: Transaction) {
    setForm({
      id: tx.id,
      account_id: tx.account_id,
      category_id: tx.category_id ?? "",
      amount: tx.amount,
      currency: tx.currency,
      transaction_type: tx.transaction_type,
      description: tx.description ?? "",
      date: tx.date.slice(0, 10),
    });
    setFormError(null);
    setFormOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    const amountNum = Number(form.amount);
    if (!Number.isFinite(amountNum) || amountNum <= 0) {
      setFormError("Amount must be a positive number.");
      return;
    }
    if (!form.account_id) {
      setFormError("Select an account.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        account_id: form.account_id,
        category_id: form.category_id || null,
        amount: amountNum,
        currency: form.currency,
        transaction_type: form.transaction_type,
        description: form.description,
        date: form.date,
      };
      if (form.id) {
        await updateTransaction(form.id, payload);
      } else {
        await createTransaction(payload);
      }
      setFormOpen(false);
      reload();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.detail : "Save failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this transaction?")) return;
    try {
      await deleteTransaction(id);
      reload();
    } catch (err) {
      window.alert(err instanceof ApiError ? err.detail : "Delete failed.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Transactions</h1>
          <div className="page-subtitle">Browse, filter, and edit transactions</div>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + New transaction
        </button>
      </div>

      <div className="card">
        <div className="filters-row">
          <div className="field">
            <label>From</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => updateFilter("date_from", e.target.value)}
            />
          </div>
          <div className="field">
            <label>To</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => updateFilter("date_to", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Category</label>
            <select
              value={filters.category_id}
              onChange={(e) => updateFilter("category_id", e.target.value)}
            >
              <option value="">All</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Account</label>
            <select
              value={filters.account_id}
              onChange={(e) => updateFilter("account_id", e.target.value)}
            >
              <option value="">All</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Type</label>
            <select
              value={filters.transaction_type}
              onChange={(e) => updateFilter("transaction_type", e.target.value)}
            >
              <option value="">All</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
          </div>
          {(filters.date_from ||
            filters.date_to ||
            filters.category_id ||
            filters.account_id ||
            filters.transaction_type) && (
            <button
              type="button"
              className="btn btn-sm"
              onClick={() => {
                setFilters(EMPTY_FILTERS);
                setOffset(0);
              }}
            >
              Clear filters
            </button>
          )}
        </div>

        {loading && <LoadingState label="Loading transactions…" />}
        {error && <ErrorState message={error} />}

        {data && (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Account</th>
                    <th>Type</th>
                    <th className="num">Amount</th>
                    <th className="col-actions">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.length === 0 && (
                    <tr className="empty-row">
                      <td colSpan={7}>No transactions match these filters.</td>
                    </tr>
                  )}
                  {data.items.map((tx) => (
                    <tr key={tx.id}>
                      <td>{formatDate(tx.date)}</td>
                      <td>{tx.description || <span className="muted">—</span>}</td>
                      <td>
                        {tx.category_id
                          ? categoryName.get(tx.category_id) ?? "—"
                          : "—"}
                      </td>
                      <td>{accountName.get(tx.account_id) ?? "—"}</td>
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
                      <td className="col-actions">
                        <button
                          type="button"
                          className="btn btn-sm"
                          onClick={() => openEdit(tx)}
                        >
                          Edit
                        </button>{" "}
                        <button
                          type="button"
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDelete(tx.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              total={data.total}
              limit={PAGE_SIZE}
              offset={offset}
              onOffsetChange={setOffset}
            />
          </>
        )}
      </div>

      {formOpen && (
        <div className="card">
          <div className="card-header">
            <h2>{form.id ? "Edit transaction" : "New transaction"}</h2>
          </div>
          {formError && <div className="callout callout-error">{formError}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="field">
                <label>Account</label>
                <select
                  value={form.account_id}
                  onChange={(e) => setForm((f) => ({ ...f, account_id: e.target.value }))}
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
                <label>Category</label>
                <select
                  value={form.category_id}
                  onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value }))}
                >
                  <option value="">Uncategorized</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Type</label>
                <select
                  value={form.transaction_type}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      transaction_type: e.target.value as TransactionType,
                    }))
                  }
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>
              <div className="field">
                <label>Amount</label>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.amount}
                  onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                  required
                />
              </div>
              <div className="field">
                <label>Currency</label>
                <input
                  type="text"
                  maxLength={3}
                  value={form.currency}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, currency: e.target.value.toUpperCase() }))
                  }
                  required
                />
              </div>
              <div className="field">
                <label>Date</label>
                <input
                  type="date"
                  value={form.date}
                  onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
                  required
                />
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Description</label>
                <input
                  type="text"
                  value={form.description}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, description: e.target.value }))
                  }
                />
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Saving…" : form.id ? "Save changes" : "Create"}
              </button>
              <button type="button" className="btn" onClick={() => setFormOpen(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
