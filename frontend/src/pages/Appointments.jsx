import { useState } from 'react';
import { api } from '../api.js';
import { Empty, ErrorBanner, PageHeader, StatusBadge } from '../components/Common.jsx';
import Modal from '../components/Modal.jsx';
import { formatDate, formatTime, todayISO, useLoader } from '../utils.js';

const STATUSES = ['SCHEDULED', 'COMPLETED', 'CANCELLED'];

function AppointmentForm({ appointment, patients, doctors, onSubmit, onCancel }) {
  const editing = Boolean(appointment);
  const bookable = doctors.filter((d) => d.is_available || d.id === appointment?.doctor_id);

  const submit = (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    onSubmit({
      patient_id: Number(f.get('patient_id')),
      doctor_id: Number(f.get('doctor_id')),
      appointment_date: f.get('appointment_date'),
      appointment_time: f.get('appointment_time'),
      reason: f.get('reason'),
      status: f.get('status') ?? 'SCHEDULED',
      notes: f.get('notes') ?? '',
    });
  };

  return (
    <form onSubmit={submit} className="form">
      <label>
        Patient
        <select name="patient_id" required defaultValue={appointment?.patient_id ?? ''}>
          <option value="" disabled>Select a patient</option>
          {patients.map((p) => <option key={p.id} value={p.id}>{p.full_name} · {p.phone}</option>)}
        </select>
      </label>
      <label>
        Doctor
        <select name="doctor_id" required defaultValue={appointment?.doctor_id ?? ''}>
          <option value="" disabled>Select a doctor</option>
          {bookable.map((d) => <option key={d.id} value={d.id}>{d.full_name} · {d.specialization}</option>)}
        </select>
      </label>
      <div className="form-row">
        <label>
          Date
          <input type="date" name="appointment_date" required defaultValue={appointment?.appointment_date ?? todayISO()} />
        </label>
        <label>
          Time
          <input type="time" name="appointment_time" required step="900"
            defaultValue={appointment?.appointment_time?.slice(0, 5) ?? '10:00'} />
        </label>
      </div>
      <label>
        Reason for visit
        <input name="reason" maxLength={500} defaultValue={appointment?.reason ?? ''} placeholder="e.g. Fever and cough" />
      </label>
      {editing && (
        <>
          <label>
            Status
            <select name="status" defaultValue={appointment.status}>
              {STATUSES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <label>
            Doctor’s notes
            <textarea name="notes" defaultValue={appointment.notes} placeholder="Diagnosis, prescription, follow-up…" />
          </label>
        </>
      )}
      <div className="form-actions">
        <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
        <button className="primary">{editing ? 'Save changes' : 'Book appointment'}</button>
      </div>
    </form>
  );
}

async function loadAll(filters) {
  const [appointments, patients, doctors] = await Promise.all([
    api.list('appointments', filters),
    api.list('patients'),
    api.list('doctors'),
  ]);
  return { appointments, patients, doctors };
}

export default function Appointments({ notify }) {
  const [filters, setFilters] = useState({ status: '', date: '' });
  const { data, error, loading, reload } = useLoader(() => loadAll(filters), [filters.status, filters.date]);
  const [editing, setEditing] = useState(null); // null = closed, {} = new, {...} = edit

  const save = async (payload) => {
    try {
      if (editing?.id) {
        await api.update('appointments', editing.id, payload);
        notify('Appointment updated');
      } else {
        await api.create('appointments', payload);
        notify('Appointment booked');
      }
      setEditing(null);
      reload();
    } catch (e) {
      notify(e.message, 'error');
    }
  };

  const setStatus = async (appt, status) => {
    try {
      await api.update('appointments', appt.id, { status });
      notify(`Marked as ${status.toLowerCase()}`);
      reload();
    } catch (e) {
      notify(e.message, 'error');
    }
  };

  const remove = async (appt) => {
    if (!window.confirm(`Delete appointment for ${appt.patient.full_name}?`)) return;
    try {
      await api.remove('appointments', appt.id);
      notify('Appointment deleted');
      reload();
    } catch (e) {
      notify(e.message, 'error');
    }
  };

  const noPeople = data && (!data.patients.length || !data.doctors.length);

  return (
    <>
      <PageHeader
        eyebrow="CLINIC / APPOINTMENTS"
        title="Appointments"
        subtitle="Book, reschedule and close patient visits."
        action={<button className="primary" disabled={!data || noPeople} onClick={() => setEditing({})}>＋ Book appointment</button>}
      />
      <ErrorBanner message={error} onRetry={reload} />
      {noPeople && <div className="alert info">Add at least one patient and one doctor before booking.</div>}

      <div className="panel">
        <div className="toolbar">
          <div className="chips">
            {['', ...STATUSES].map((s) => (
              <button key={s || 'ALL'} className={filters.status === s ? 'selected' : ''}
                onClick={() => setFilters({ ...filters, status: s })}>
                {s ? s.charAt(0) + s.slice(1).toLowerCase() : 'All'}
              </button>
            ))}
          </div>
          <div className="toolbar-right">
            <input type="date" aria-label="Filter by date" value={filters.date}
              onChange={(e) => setFilters({ ...filters, date: e.target.value })} />
            <button className="ghost" onClick={() => setFilters({ ...filters, date: todayISO() })}>Today</button>
            {filters.date && <button className="ghost" onClick={() => setFilters({ ...filters, date: '' })}>Clear</button>}
          </div>
        </div>

        {loading && !data ? <Empty>Loading appointments…</Empty> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>When</th><th>Patient</th><th>Doctor</th><th>Reason</th><th>Status</th><th aria-label="Actions" /></tr>
              </thead>
              <tbody>
                {data?.appointments.map((a) => (
                  <tr key={a.id}>
                    <td><b>{formatDate(a.appointment_date)}</b><small>{formatTime(a.appointment_time)}</small></td>
                    <td><b>{a.patient.full_name}</b><small>{a.patient.phone}</small></td>
                    <td><b>{a.doctor.full_name}</b><small>{a.doctor.specialization}</small></td>
                    <td className="wrap">{a.reason || '—'}{a.notes && <small>📝 {a.notes}</small>}</td>
                    <td><StatusBadge status={a.status} /></td>
                    <td className="actions">
                      {a.status === 'SCHEDULED' && (
                        <>
                          <button className="icon-btn ok" title="Mark completed" onClick={() => setStatus(a, 'COMPLETED')}>✓</button>
                          <button className="icon-btn warn" title="Cancel" onClick={() => setStatus(a, 'CANCELLED')}>⊘</button>
                        </>
                      )}
                      <button className="icon-btn" title="Edit" onClick={() => setEditing(a)}>✎</button>
                      <button className="icon-btn danger" title="Delete" onClick={() => remove(a)}>🗑</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!data?.appointments.length && <Empty>No appointments match these filters.</Empty>}
          </div>
        )}
      </div>

      {editing && data && (
        <Modal eyebrow={editing.id ? 'EDIT APPOINTMENT' : 'NEW APPOINTMENT'}
          title={editing.id ? editing.patient.full_name : 'Book an appointment'} onClose={() => setEditing(null)}>
          <AppointmentForm appointment={editing.id ? editing : null} patients={data.patients} doctors={data.doctors}
            onSubmit={save} onCancel={() => setEditing(null)} />
        </Modal>
      )}
    </>
  );
}
