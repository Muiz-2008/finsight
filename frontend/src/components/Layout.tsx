import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import type { Theme } from "../hooks/useTheme";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/transactions", label: "Transactions" },
  { to: "/transactions/import", label: "Import CSV" },
  { to: "/budgets", label: "Budgets" },
  { to: "/portfolio", label: "Portfolio" },
  { to: "/portfolio/analytics", label: "Portfolio Analytics" },
  { to: "/backtesting", label: "Backtesting" },
  { to: "/insights", label: "Insights" },
  { to: "/settings", label: "Settings" },
];

const THEME_OPTIONS: { value: Theme; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "Auto" },
];

export function Layout() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">FinSight</div>
          <div className="sidebar-brand-sub">Portfolio &amp; risk analytics</div>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `sidebar-link${isActive ? " active" : ""}`
              }
              // Exact match always: every nav route here is an independent
              // sibling page (see App.tsx), not a parent/child pair, but
              // "/transactions" is still a string-prefix of
              // "/transactions/import" (same for "/portfolio" and
              // "/portfolio/analytics") — without `end`, NavLink's default
              // prefix matching highlighted both links at once.
              end
            >
              <span className="dot" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="theme-toggle" role="group" aria-label="Theme">
          {THEME_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`theme-toggle-btn${theme === opt.value ? " active" : ""}`}
              onClick={() => setTheme(opt.value)}
              aria-pressed={theme === opt.value}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className="sidebar-footer">{user?.email}</div>
      </aside>
      <div className="main-col">
        <Outlet />
      </div>
    </div>
  );
}
