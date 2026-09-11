import { useAuth } from "../hooks/useAuth";
import { formatDate } from "../lib/format";

export default function Settings() {
  const { user, logout } = useAuth();

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <div className="page-subtitle">Account details</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 420 }}>
        <div className="form-grid" style={{ gridTemplateColumns: "1fr" }}>
          <div className="field">
            <label>Email</label>
            <div>{user?.email}</div>
          </div>
          <div className="field">
            <label>Full name</label>
            <div>{user?.full_name || <span className="muted">Not set</span>}</div>
          </div>
          <div className="field">
            <label>Member since</label>
            <div>{formatDate(user?.created_at)}</div>
          </div>
        </div>
        <div className="form-actions">
          <button type="button" className="btn btn-danger" onClick={logout}>
            Log out
          </button>
        </div>
      </div>

      <p className="muted" style={{ fontSize: 12, maxWidth: 420 }}>
        Session tokens are stored in your browser's local storage for this
        project. That is a known limitation, not a production-grade choice —
        it is vulnerable to token theft via XSS and would be replaced with an
        httpOnly cookie in a real deployment.
      </p>
    </div>
  );
}
