import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useAsync } from "../hooks/useAsync";
import {
  createPortfolio,
  getPerformance,
  listKnownSymbols,
  listPortfolios,
  recordTrade,
} from "../api/endpoints";
import type { TradeType } from "../types/api";
import { ApiError } from "../api/client";
import { formatCurrency, formatNumber, formatSignedCurrency, signClass } from "../lib/format";
import { LoadingState, ErrorState } from "../components/LoadingState";

interface TradeForm {
  symbol: string;
  trade_type: TradeType;
  quantity: string;
  price: string;
  fees: string;
  trade_date: string;
}

function blankTrade(): TradeForm {
  return {
    symbol: "",
    trade_type: "buy",
    quantity: "",
    price: "",
    fees: "0",
    trade_date: new Date().toISOString().slice(0, 10),
  };
}

export default function Portfolio() {
  const [params, setParams] = useSearchParams();
  const selectedId = params.get("portfolio") ?? "";

  const { data: portfolios, loading: loadingPortfolios, error: portfoliosError, reload: reloadPortfolios } =
    useAsync(useCallback(() => listPortfolios(), []), []);

  useEffect(() => {
    if (!selectedId && portfolios && portfolios.length > 0) {
      setParams({ portfolio: portfolios[0].id }, { replace: true });
    }
  }, [selectedId, portfolios, setParams]);

  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [tradeForm, setTradeForm] = useState<TradeForm>(blankTrade());
  const [tradeError, setTradeError] = useState<string | null>(null);
  const [tradeSubmitting, setTradeSubmitting] = useState(false);

  // A curated list, not free text: the API rejects any symbol it doesn't
  // recognize (see backend/app/market_data/known_symbols.py), so letting
  // someone type an arbitrary string here just meant discovering the typo
  // after submitting instead of before.
  const { data: knownSymbols } = useAsync(useCallback(() => listKnownSymbols(), []), []);

  const loadPerf = useCallback(() => {
    if (!selectedId) return Promise.resolve(null);
    return getPerformance(selectedId);
  }, [selectedId]);
  const { data: performance, loading: loadingPerf, error: perfError, reload: reloadPerf } =
    useAsync(loadPerf, [selectedId]);

  async function handleCreatePortfolio(e: FormEvent) {
    e.preventDefault();
    setCreateError(null);
    if (!newName.trim()) {
      setCreateError("Name is required.");
      return;
    }
    setCreating(true);
    try {
      const p = await createPortfolio(newName.trim());
      setNewName("");
      reloadPortfolios();
      setParams({ portfolio: p.id });
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.detail : "Create failed.");
    } finally {
      setCreating(false);
    }
  }

  async function handleTrade(e: FormEvent) {
    e.preventDefault();
    setTradeError(null);
    if (!selectedId) return;
    const quantity = Number(tradeForm.quantity);
    const price = Number(tradeForm.price);
    const fees = Number(tradeForm.fees || "0");
    if (!tradeForm.symbol.trim()) {
      setTradeError("Symbol is required.");
      return;
    }
    if (!Number.isFinite(quantity) || quantity <= 0) {
      setTradeError("Quantity must be a positive number.");
      return;
    }
    if (!Number.isFinite(price) || price <= 0) {
      setTradeError("Price must be a positive number.");
      return;
    }
    setTradeSubmitting(true);
    try {
      await recordTrade(selectedId, {
        symbol: tradeForm.symbol.trim().toUpperCase(),
        trade_type: tradeForm.trade_type,
        quantity,
        price,
        fees: Number.isFinite(fees) ? fees : 0,
        trade_date: tradeForm.trade_date,
      });
      setTradeForm(blankTrade());
      reloadPerf();
    } catch (err) {
      setTradeError(err instanceof ApiError ? err.detail : "Trade failed.");
    } finally {
      setTradeSubmitting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Portfolio</h1>
          <div className="page-subtitle">Positions, trades, and market value</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Portfolios</h2>
        </div>
        {loadingPortfolios && <LoadingState label="Loading portfolios…" />}
        {portfoliosError && <ErrorState message={portfoliosError} />}
        {portfolios && (
          <div className="filters-row" style={{ marginBottom: 0 }}>
            <div className="field">
              <label>Select portfolio</label>
              <select
                value={selectedId}
                onChange={(e) => setParams({ portfolio: e.target.value })}
              >
                {portfolios.length === 0 && <option value="">No portfolios yet</option>}
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <form onSubmit={handleCreatePortfolio} style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              <div className="field">
                <label>New portfolio</label>
                <input
                  type="text"
                  placeholder="e.g. Retirement"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />
              </div>
              <button type="submit" className="btn" disabled={creating}>
                {creating ? "Creating…" : "Create"}
              </button>
            </form>
          </div>
        )}
        {createError && <div className="callout callout-error">{createError}</div>}
      </div>

      {selectedId && (
        <>
          <div className="card">
            <div className="card-header">
              <h2>Positions</h2>
            </div>
            {loadingPerf && <LoadingState label="Loading positions…" />}
            {perfError && <ErrorState message={perfError} />}
            {performance && (
              <>
                <div className="stat-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
                  <div className="stat-tile">
                    <div className="stat-label">Market value</div>
                    <div className="stat-value">{formatCurrency(performance.total_market_value)}</div>
                  </div>
                  <div className="stat-tile">
                    <div className="stat-label">Cost basis</div>
                    <div className="stat-value">{formatCurrency(performance.total_cost_basis)}</div>
                  </div>
                  <div className="stat-tile">
                    <div className="stat-label">Unrealized P/L</div>
                    <div className={`stat-value ${signClass(performance.total_unrealized_pl)}`}>
                      {formatSignedCurrency(performance.total_unrealized_pl)}
                    </div>
                  </div>
                  <div className="stat-tile">
                    <div className="stat-label">Realized P/L</div>
                    <div className={`stat-value ${signClass(performance.total_realized_pl)}`}>
                      {formatSignedCurrency(performance.total_realized_pl)}
                    </div>
                  </div>
                </div>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th className="num">Quantity</th>
                        <th className="num">Avg cost</th>
                        <th className="num">Current price</th>
                        <th className="num">Market value</th>
                        <th className="num">Unrealized P/L</th>
                        <th className="num">Realized P/L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {performance.positions.length === 0 && (
                        <tr className="empty-row">
                          <td colSpan={7}>No open positions.</td>
                        </tr>
                      )}
                      {performance.positions.map((pos) => (
                        <tr key={pos.symbol}>
                          <td>
                            <strong>{pos.symbol}</strong>
                          </td>
                          <td className="num">{formatNumber(pos.quantity, 4)}</td>
                          <td className="num">{formatCurrency(pos.avg_cost)}</td>
                          <td className="num">{formatCurrency(pos.current_price)}</td>
                          <td className="num">{formatCurrency(pos.market_value)}</td>
                          <td className={`num ${signClass(pos.unrealized_pl)}`}>
                            {formatSignedCurrency(pos.unrealized_pl)}
                          </td>
                          <td className={`num ${signClass(pos.realized_pl)}`}>
                            {formatSignedCurrency(pos.realized_pl)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>

          <div className="card" style={{ maxWidth: 560 }}>
            <div className="card-header">
              <h2>Record a trade</h2>
            </div>
            {tradeError && <div className="callout callout-error">{tradeError}</div>}
            <form onSubmit={handleTrade}>
              <div className="form-grid">
                <div className="field">
                  <label>Symbol</label>
                  <select
                    value={tradeForm.symbol}
                    onChange={(e) => setTradeForm((f) => ({ ...f, symbol: e.target.value }))}
                    required
                  >
                    <option value="" disabled>
                      Select a symbol…
                    </option>
                    {(knownSymbols ?? []).map((s) => (
                      <option key={s.symbol} value={s.symbol}>
                        {s.symbol} — {s.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Side</label>
                  <select
                    value={tradeForm.trade_type}
                    onChange={(e) =>
                      setTradeForm((f) => ({ ...f, trade_type: e.target.value as TradeType }))
                    }
                  >
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                  </select>
                </div>
                <div className="field">
                  <label>Quantity</label>
                  <input
                    type="number"
                    min="0.0001"
                    step="0.0001"
                    value={tradeForm.quantity}
                    onChange={(e) => setTradeForm((f) => ({ ...f, quantity: e.target.value }))}
                    required
                  />
                </div>
                <div className="field">
                  <label>Price</label>
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={tradeForm.price}
                    onChange={(e) => setTradeForm((f) => ({ ...f, price: e.target.value }))}
                    required
                  />
                </div>
                <div className="field">
                  <label>Fees</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={tradeForm.fees}
                    onChange={(e) => setTradeForm((f) => ({ ...f, fees: e.target.value }))}
                  />
                </div>
                <div className="field">
                  <label>Trade date</label>
                  <input
                    type="date"
                    value={tradeForm.trade_date}
                    onChange={(e) => setTradeForm((f) => ({ ...f, trade_date: e.target.value }))}
                    required
                  />
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-primary" disabled={tradeSubmitting}>
                  {tradeSubmitting ? "Recording…" : "Record trade"}
                </button>
              </div>
            </form>
          </div>
        </>
      )}
    </div>
  );
}
