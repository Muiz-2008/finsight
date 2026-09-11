import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoadingState } from "./components/LoadingState";

const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Transactions = lazy(() => import("./pages/Transactions"));
const TransactionImport = lazy(() => import("./pages/TransactionImport"));
const Budgets = lazy(() => import("./pages/Budgets"));
const Portfolio = lazy(() => import("./pages/Portfolio"));
const PortfolioAnalytics = lazy(() => import("./pages/PortfolioAnalytics"));
const Backtesting = lazy(() => import("./pages/Backtesting"));
const Insights = lazy(() => import("./pages/Insights"));
const Settings = lazy(() => import("./pages/Settings"));

function PageFallback() {
  return (
    <div className="page">
      <LoadingState />
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/transactions/import" element={<TransactionImport />} />
            <Route path="/budgets" element={<Budgets />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/portfolio/analytics" element={<PortfolioAnalytics />} />
            <Route path="/backtesting" element={<Backtesting />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Route>

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}
