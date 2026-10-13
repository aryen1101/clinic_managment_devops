export default function Sidebar({ pages, current, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">✚</span>
        <div>
          <b>CareDesk</b>
          <small>Clinic Management</small>
        </div>
      </div>
      <nav>
        {Object.entries(pages).map(([key, page]) => (
          <button
            key={key}
            className={current === key ? 'active' : ''}
            onClick={() => onNavigate(key)}
            aria-current={current === key ? 'page' : undefined}
          >
            <span className="nav-icon" aria-hidden="true">{page.icon}</span>
            <span>{page.label}</span>
          </button>
        ))}
      </nav>
      <div className="side-footer">
        <div className="avatar">FD</div>
        <div>
          <b>Front Desk</b>
          <small>Reception</small>
        </div>
      </div>
    </aside>
  );
}
