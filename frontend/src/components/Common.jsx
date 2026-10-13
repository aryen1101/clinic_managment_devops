export function PageHeader({ eyebrow, title, subtitle, action }) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}

export function StatCard({ label, value, hint, icon, tone = 'teal' }) {
  return (
    <div className="stat">
      <div className={`stat-icon ${tone}`} aria-hidden="true">{icon}</div>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
        {hint && <span>{hint}</span>}
      </div>
    </div>
  );
}

export function StatusBadge({ status }) {
  return <span className={`badge ${status.toLowerCase()}`}>{status.charAt(0) + status.slice(1).toLowerCase()}</span>;
}

export function ErrorBanner({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="alert">
      <span>⚠ {message}</span>
      {onRetry && <button className="ghost" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export function Empty({ children }) {
  return <div className="empty">{children}</div>;
}
