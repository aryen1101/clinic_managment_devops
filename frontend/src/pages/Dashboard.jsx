import { api, systemStatus } from '../api.js';
import { Empty, ErrorBanner, PageHeader, StatCard, StatusBadge } from '../components/Common.jsx';
import { formatTime, initials, todayISO, useLoader } from '../utils.js';

async function loadDashboard() {
  const [stats, today, health] = await Promise.all([
    api.stats(),
    api.list('appointments', { date: todayISO() }),
    systemStatus(),
  ]);
  return { stats, today, health };
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function Dashboard({ onNavigate }) {
  const { data, error, loading, reload } = useLoader(loadDashboard, []);
  const stats = data?.stats;
  const totalAppointments = stats ? stats.scheduled + stats.completed + stats.cancelled : 0;
  const pct = (n) => (totalAppointments ? Math.round((n / totalAppointments) * 100) : 0);

  return (
    <>
      <PageHeader
        eyebrow="CLINIC / OVERVIEW"
        title={`${greeting()} 👋`}
        subtitle="Here’s what’s happening at the clinic today."
        action={<button className="primary" onClick={() => onNavigate('appointments')}>＋ Book appointment</button>}
      />
      <ErrorBanner message={error && `${error}. Is the backend running?`} onRetry={reload} />

      <section className="stats">
        <StatCard label="Patients" value={stats?.total_patients ?? '–'} hint="Registered" icon="♥" tone="rose" />
        <StatCard
          label="Doctors"
          value={stats?.total_doctors ?? '–'}
          hint={stats ? `${stats.available_doctors} available` : ''}
          icon="⚕"
          tone="blue"
        />
        <StatCard label="Today" value={stats?.appointments_today ?? '–'} hint="Appointments" icon="◷" tone="amber" />
        <StatCard label="Upcoming" value={stats?.scheduled ?? '–'} hint="Scheduled" icon="✓" tone="teal" />
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>Today’s appointments</h2>
              <p className="muted">{new Date().toDateString()}</p>
            </div>
            <button className="ghost" onClick={() => onNavigate('appointments')}>View all →</button>
          </div>
          {loading && !data ? (
            <Empty>Loading…</Empty>
          ) : !data?.today?.length ? (
            <Empty>No appointments today.</Empty>
          ) : (
            <ul className="timeline">
              {data.today.map((a) => (
                <li key={a.id}>
                  <span className="time">{formatTime(a.appointment_time)}</span>
                  <span className="avatar small">{initials(a.patient.full_name)}</span>
                  <div className="grow">
                    <b>{a.patient.full_name}</b>
                    <small>{a.doctor.full_name} · {a.reason || a.doctor.specialization}</small>
                  </div>
                  <StatusBadge status={a.status} />
                </li>
              ))}
            </ul>
          )}
        </div>

        <aside className="side-panels">
          <div className="panel">
            <h2>Appointment status</h2>
            <p className="muted">{totalAppointments} total</p>
            {[
              ['Scheduled', stats?.scheduled ?? 0, 'scheduled'],
              ['Completed', stats?.completed ?? 0, 'completed'],
              ['Cancelled', stats?.cancelled ?? 0, 'cancelled'],
            ].map(([label, n, cls]) => (
              <div className="bar-row" key={label}>
                <div className="bar-label"><span>{label}</span><b>{n}</b></div>
                <div className="bar"><i className={cls} style={{ width: `${pct(n)}%` }} /></div>
              </div>
            ))}
          </div>

          <div className="panel">
            <h2>Platform health</h2>
            <p className="muted">Live checks against the backend</p>
            <div className="health-row">
              <span className={`dot ${data?.health?.api ? 'up' : 'down'}`} /> API <code>/health</code>
              <b>{data?.health?.api ? 'UP' : 'DOWN'}</b>
            </div>
            <div className="health-row">
              <span className={`dot ${data?.health?.db ? 'up' : 'down'}`} /> Database <code>/ready</code>
              <b>{data?.health?.db ? 'UP' : 'DOWN'}</b>
            </div>
            <div className="pipeline" aria-label="Delivery pipeline">
              <span>Test</span><i /><span>Scan</span><i /><span>Build</span><i /><span>Deploy</span>
            </div>
          </div>
        </aside>
      </section>
    </>
  );
}
