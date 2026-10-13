import { useCallback, useEffect, useState } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Appointments from './pages/Appointments.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Doctors from './pages/Doctors.jsx';
import Patients from './pages/Patients.jsx';

const PAGES = {
  dashboard: { label: 'Dashboard', icon: '▦', component: Dashboard },
  appointments: { label: 'Appointments', icon: '◷', component: Appointments },
  patients: { label: 'Patients', icon: '♥', component: Patients },
  doctors: { label: 'Doctors', icon: '⚕', component: Doctors },
};

function initialPage() {
  const hash = window.location.hash.replace('#', '');
  return PAGES[hash] ? hash : 'dashboard';
}

export default function App() {
  const [page, setPage] = useState(initialPage);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    window.location.hash = page;
  }, [page]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(timer);
  }, [toast]);

  const notify = useCallback((message, type = 'success') => setToast({ message, type, at: Date.now() }), []);
  const Page = PAGES[page].component;

  return (
    <div className="app">
      <Sidebar pages={PAGES} current={page} onNavigate={setPage} />
      <main className="main">
        <Page key={page} notify={notify} onNavigate={setPage} />
      </main>
      {toast && <div className={`toast ${toast.type}`} role="status">{toast.message}</div>}
    </div>
  );
}
