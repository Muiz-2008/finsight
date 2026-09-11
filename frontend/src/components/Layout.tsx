import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

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

export function Layout() {
  const { user } = useAuth();

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
              end={item.to === "/dashboard"}
            >
              <span className="dot" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">{user?.email}</div>
      </aside>
      <div className="main-col">
        <Outlet />
      </div>
    </div>
  );
}
