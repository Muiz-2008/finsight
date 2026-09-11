// Types mirroring the FinSight backend API (see backend OpenAPI docs at /docs).
// Amounts that the API returns as decimal strings are typed as `string` here;
// convert with `Number(...)` at the point of use for arithmetic/formatting.

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export type AccountType =
  | "checking"
  | "savings"
  | "credit_card"
  | "cash"
  | "investment"
  | "other";

export interface Account {
  id: string;
  name: string;
  account_type: AccountType;
  currency: string;
}

export interface Category {
  id: string;
  name: string;
}

export type TransactionType = "income" | "expense";

export interface Transaction {
  id: string;
  account_id: string;
  category_id: string | null;
  amount: string;
  currency: string;
  transaction_type: TransactionType;
  description: string | null;
  date: string;
  created_at: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface TransactionCreate {
  account_id: string;
  category_id?: string | null;
  amount: number;
  currency: string;
  transaction_type: TransactionType;
  description?: string;
  date: string;
}

export interface ImportReport {
  total_rows: number;
  imported: number;
  duplicates: number;
  invalid: number;
  errors: string[];
}

export interface Budget {
  id: string;
  category_id: string;
  monthly_limit: string;
}

export interface CashflowSummary {
  date_from: string;
  date_to: string;
  income: string;
  expenses: string;
  net_cashflow: string;
  savings_rate: number | null;
}

export interface MonthlyCashflow {
  month: string;
  income: string;
  expenses: string;
  net: string;
}

export interface SpendingByCategory {
  category: string;
  total: string;
  percentage_of_spending: number;
}

export interface SpendingSummary {
  date_from: string;
  date_to: string;
  by_category: SpendingByCategory[];
  largest_transactions: Transaction[];
}

export type BudgetStatus = "under" | "approaching" | "over";

export interface BudgetAnalytics {
  category: string;
  budgeted: string;
  actual: string;
  status: BudgetStatus;
}

export interface Anomaly {
  transaction: Transaction;
  category: string;
  method: string;
  reason: string;
}

export interface Portfolio {
  id: string;
  name: string;
}

export type TradeType = "buy" | "sell";

export interface TradeCreate {
  symbol: string;
  trade_type: TradeType;
  quantity: number;
  price: number;
  fees: number;
  trade_date: string;
}

export interface Position {
  symbol: string;
  quantity: string;
  avg_cost: string;
  cost_basis: string;
  current_price: string | null;
  market_value: string | null;
  unrealized_pl: string | null;
  realized_pl: string;
}

export interface PortfolioPerformance {
  portfolio_id: string;
  positions: Position[];
  total_market_value: string;
  total_cost_basis: string;
  total_unrealized_pl: string;
  total_realized_pl: string;
}

export interface CorrelationMatrix {
  [symbol: string]: { [symbol: string]: number };
}

export interface PortfolioRisk {
  portfolio_id: string;
  lookback_days: number;
  date_from: string | null;
  date_to: string | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  cumulative_return: number | null;
  correlation_matrix: CorrelationMatrix | null;
  warning: string | null;
}

export interface PortfolioBenchmark {
  portfolio_id: string;
  benchmark_symbol: string;
  lookback_days: number;
  date_from: string | null;
  date_to: string | null;
  portfolio_return: number | null;
  benchmark_return: number | null;
  outperformance: number | null;
  portfolio_volatility: number | null;
  benchmark_volatility: number | null;
  portfolio_max_drawdown: number | null;
  benchmark_max_drawdown: number | null;
  beta: number | null;
  warning: string | null;
}

export interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital?: number;
  short_window?: number;
  long_window?: number;
  transaction_cost_bps?: number;
}

export interface BacktestResult {
  symbol: string;
  start_date: string;
  end_date: string;
  strategy: string;
  final_value: number;
  total_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  num_trades: number;
  equity_curve: number[];
  disclaimer: string;
}

export type InsightCategory = "spending" | "budget" | "savings" | "portfolio";

export interface Insight {
  id: string;
  category: InsightCategory;
  message: string;
  created_at: string;
}
