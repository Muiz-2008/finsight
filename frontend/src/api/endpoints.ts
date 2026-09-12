import { api } from "./client";
import type {
  Account,
  AccountType,
  Anomaly,
  BacktestRequest,
  BacktestResult,
  Budget,
  BudgetAnalytics,
  CashflowSummary,
  Category,
  ImportReport,
  Insight,
  KnownSymbol,
  MonthlyCashflow,
  Portfolio,
  PortfolioBenchmark,
  PortfolioPerformance,
  PortfolioRisk,
  SpendingSummary,
  TradeCreate,
  Transaction,
  TransactionCreate,
  TransactionListResponse,
  User,
} from "../types/api";

// --- Auth ---

export function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  return api.postForm<{ access_token: string; token_type: string }>(
    "/api/v1/auth/login",
    form,
  );
}

export function register(email: string, password: string, full_name?: string) {
  return api.post<User>("/api/v1/auth/register", { email, password, full_name });
}

export function getMe() {
  return api.get<User>("/api/v1/users/me");
}

// --- Accounts ---

export function listAccounts() {
  return api.get<Account[]>("/api/v1/accounts");
}

export function createAccount(data: {
  name: string;
  account_type: AccountType;
  currency: string;
}) {
  return api.post<Account>("/api/v1/accounts", data);
}

// --- Categories ---

export function listCategories() {
  return api.get<Category[]>("/api/v1/categories");
}

export function createCategory(name: string) {
  return api.post<Category>("/api/v1/categories", { name });
}

// --- Transactions ---

export interface TransactionFilters {
  date_from?: string;
  date_to?: string;
  category_id?: string;
  account_id?: string;
  transaction_type?: string;
  limit?: number;
  offset?: number;
  sort_desc?: boolean;
}

export function listTransactions(filters: TransactionFilters = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return api.get<TransactionListResponse>(
    `/api/v1/transactions${qs ? `?${qs}` : ""}`,
  );
}

export function createTransaction(data: TransactionCreate) {
  return api.post<Transaction>("/api/v1/transactions", data);
}

export function updateTransaction(id: string, data: Partial<TransactionCreate>) {
  return api.put<Transaction>(`/api/v1/transactions/${id}`, data);
}

export function deleteTransaction(id: string) {
  return api.delete<void>(`/api/v1/transactions/${id}`);
}

export function importTransactions(accountId: string, file: File) {
  const formData = new FormData();
  formData.set("account_id", accountId);
  formData.set("file", file);
  return api.postFormData<ImportReport>("/api/v1/transactions/import", formData);
}

// --- Budgets ---

export function listBudgets() {
  return api.get<Budget[]>("/api/v1/budgets");
}

export function upsertBudget(category_id: string, monthly_limit: number) {
  return api.post<Budget>("/api/v1/budgets", { category_id, monthly_limit });
}

// --- Analytics ---

export function getCashflow(date_from?: string, date_to?: string) {
  const params = new URLSearchParams();
  if (date_from) params.set("date_from", date_from);
  if (date_to) params.set("date_to", date_to);
  const qs = params.toString();
  return api.get<CashflowSummary>(
    `/api/v1/analytics/cashflow${qs ? `?${qs}` : ""}`,
  );
}

export function getMonthlyCashflow(date_from?: string, date_to?: string) {
  const params = new URLSearchParams();
  if (date_from) params.set("date_from", date_from);
  if (date_to) params.set("date_to", date_to);
  const qs = params.toString();
  return api.get<MonthlyCashflow[]>(
    `/api/v1/analytics/cashflow/monthly${qs ? `?${qs}` : ""}`,
  );
}

export function getSpending(date_from?: string, date_to?: string) {
  const params = new URLSearchParams();
  if (date_from) params.set("date_from", date_from);
  if (date_to) params.set("date_to", date_to);
  const qs = params.toString();
  return api.get<SpendingSummary>(
    `/api/v1/analytics/spending${qs ? `?${qs}` : ""}`,
  );
}

export function getBudgetAnalytics(date_from?: string, date_to?: string) {
  const params = new URLSearchParams();
  if (date_from) params.set("date_from", date_from);
  if (date_to) params.set("date_to", date_to);
  const qs = params.toString();
  return api.get<BudgetAnalytics[]>(
    `/api/v1/analytics/budgets${qs ? `?${qs}` : ""}`,
  );
}

export function getAnomalies(method: "zscore" | "iqr" = "zscore", lookback_days = 90) {
  const params = new URLSearchParams({ method, lookback_days: String(lookback_days) });
  return api.get<Anomaly[]>(`/api/v1/analytics/anomalies?${params.toString()}`);
}

// --- Assets ---

export function listKnownSymbols() {
  return api.get<KnownSymbol[]>("/api/v1/assets/symbols");
}

// --- Portfolios ---

export function listPortfolios() {
  return api.get<Portfolio[]>("/api/v1/portfolios");
}

export function createPortfolio(name: string) {
  return api.post<Portfolio>("/api/v1/portfolios", { name });
}

export function recordTrade(portfolioId: string, data: TradeCreate) {
  return api.post<unknown>(`/api/v1/portfolios/${portfolioId}/trades`, data);
}

export function getPerformance(portfolioId: string) {
  return api.get<PortfolioPerformance>(
    `/api/v1/portfolios/${portfolioId}/performance`,
  );
}

export function getRisk(portfolioId: string, lookback_days = 252) {
  return api.get<PortfolioRisk>(
    `/api/v1/portfolios/${portfolioId}/risk?lookback_days=${lookback_days}`,
  );
}

export function getBenchmark(
  portfolioId: string,
  symbol = "SPY",
  lookback_days = 252,
) {
  const params = new URLSearchParams({ symbol, lookback_days: String(lookback_days) });
  return api.get<PortfolioBenchmark>(
    `/api/v1/portfolios/${portfolioId}/benchmark?${params.toString()}`,
  );
}

// --- Backtesting ---

export function runBacktest(data: BacktestRequest) {
  return api.post<BacktestResult>("/api/v1/backtests", data);
}

// --- Insights ---

export function getInsights() {
  return api.get<Insight[]>("/api/v1/insights");
}
