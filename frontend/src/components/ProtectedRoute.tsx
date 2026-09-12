import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LoadingState } from "./LoadingState";

export function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="auth-shell">
        <LoadingState label="Checking session…" />
      </div>
    );
  }

  if (!user) {
    // Login.tsx reads location.state.from to send the user back to
    // wherever they were headed — without setting it here, that logic
    // was dead code and every login landed on /dashboard regardless of
    // which page originally redirected here.
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return <Outlet />;
}
