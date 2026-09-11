import { useCallback, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useAsync } from "../hooks/useAsync";
import { getBenchmark, getRisk, listPortfolios } from "../api/endpoints";
import { formatNumber, formatPercent, signClass } from "../lib/format";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { CorrelationHeatmap } from "../components/charts/CorrelationHeatmap";

export default function PortfolioAnalytics() {
  const [params, setParams] = useSearchParams();
  const selectedId = params.get("portfolio") ?? "";

  const { data: portfolios, loading: loadingPortfolios, error: portfoliosError } =
    useAsync(useCallback(() => listPortfolios(), []), []);

  useEffect(() => {
    if (!selectedId && portfolios && portfolios.length > 0) {
      setParams({ portfolio: portfolios[0].id }, { replace: true });
    }
  }, [selectedId, portfolios, setParams]);

  const loadRisk = useCallback(() => {
    if (!selectedId) return Promise.resolve(null);
    return getRisk(selectedId, 252);
  }, [selectedId]);
  const { data: risk, loading: loadingRisk, error: riskError } = useAsync(loadRisk, [selectedId]);

  const loadBenchmark = useCallback(() => {
    if (!selectedId) return Promise.resolve(null);
    return getBenchmark(selectedId, "SPY", 252);
  }, [selectedId]);
  const { data: benchmark, loading: loadingBenchmark, error: benchmarkError } =
    useAsync(loadBenchmark, [selectedId]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Portfolio Analytics</h1>
          <div className="page-subtitle">Risk, correlation, and benchmark comparison</div>
        </div>
      </div>

      <div className="card">
        {loadingPortfolios && <LoadingState label="Loading portfolios…" />}
        {portfoliosError && <ErrorState message={portfoliosError} />}
        {portfolios && (
          <div className="field" style={{ maxWidth: 280 }}>
            <label>Portfolio</label>
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
        )}
      </div>

      {selectedId && (
        <>
          <div className="card">
            <div className="card-header">
              <h2>Risk metrics</h2>
              <span className="card-header-sub">Lookback: 252 trading days</span>
            </div>
            {loadingRisk && <LoadingState label="Loading risk metrics…" />}
            {riskError && <ErrorState message={riskError} />}
            {risk && (
              <>
                {risk.warning && <div className="callout callout-warning">{risk.warning}</div>}
                <div className="stat-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
                  <div className="stat-tile">
                    <div className="stat-label">Annualized volatility</div>
                    <div className="stat-value">{formatPercent(risk.annualized_volatility)}</div>
                  </div>
                  <div className="stat-tile">
                    <div className="stat-label">Sharpe ratio</div>
                    <div className="stat-value">{formatNumber(risk.sharpe_ratio)}</div>
                  </div>
                  <div className="stat-tile">
                    <div className="stat-label">Max drawdown</div>
                    <div className="stat-value negative">{formatPercent(risk.max_drawdown)}</div>
                  </div>
                  <div className="stat-tile">
                    <div className="stat-label">Cumulative return</div>
                    <div className={`stat-value ${signClass(risk.cumulative_return)}`}>
                      {formatPercent(risk.cumulative_return)}
                    </div>
                  </div>
                </div>

                <h3 style={{ marginTop: 18, marginBottom: 8 }}>Correlation matrix</h3>
                {risk.correlation_matrix ? (
                  <CorrelationHeatmap matrix={risk.correlation_matrix} />
                ) : (
                  <p className="muted">Not enough positions for a correlation matrix.</p>
                )}
              </>
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h2>Benchmark comparison</h2>
              <span className="card-header-sub">vs. SPY</span>
            </div>
            {loadingBenchmark && <LoadingState label="Loading benchmark comparison…" />}
            {benchmarkError && <ErrorState message={benchmarkError} />}
            {benchmark && (
              <>
                {benchmark.warning && (
                  <div className="callout callout-warning">{benchmark.warning}</div>
                )}
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th></th>
                        <th className="num">Portfolio</th>
                        <th className="num">{benchmark.benchmark_symbol}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>Return</td>
                        <td className={`num ${signClass(benchmark.portfolio_return)}`}>
                          {formatPercent(benchmark.portfolio_return)}
                        </td>
                        <td className={`num ${signClass(benchmark.benchmark_return)}`}>
                          {formatPercent(benchmark.benchmark_return)}
                        </td>
                      </tr>
                      <tr>
                        <td>Volatility</td>
                        <td className="num">{formatPercent(benchmark.portfolio_volatility)}</td>
                        <td className="num">{formatPercent(benchmark.benchmark_volatility)}</td>
                      </tr>
                      <tr>
                        <td>Max drawdown</td>
                        <td className="num negative">
                          {formatPercent(benchmark.portfolio_max_drawdown)}
                        </td>
                        <td className="num negative">
                          {formatPercent(benchmark.benchmark_max_drawdown)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="stat-grid" style={{ gridTemplateColumns: "repeat(2, 1fr)", marginTop: 12 }}>
                  <div className="stat-tile">
                    <div className="stat-label">Outperformance</div>
                    <div className={`stat-value ${signClass(benchmark.outperformance)}`}>
                      {formatPercent(benchmark.outperformance)}
                    </div>
                  </div>
                  <div className="stat-tile">
                    <div className="stat-label">Beta</div>
                    <div className="stat-value">{formatNumber(benchmark.beta)}</div>
                  </div>
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
