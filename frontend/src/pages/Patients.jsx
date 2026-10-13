import { useState } from 'react';
import { api } from '../api.js';
import { Empty, ErrorBanner, PageHeader, StatusBadge } from '../components/Common.jsx';
import Modal from '../components/Modal.jsx';
import { age, emptyToNull, formatDate, formatTime, initials, useLoader } from '../utils.js';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

function PatientForm({ patient, onSubmit, onCancel }) {
  const submit = (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    onSubmit({
      full_name: f.get('full_name').trim(),
      date_of_birth: f.get('date_of_birth'),
      gender: f.get('gender'),
      phone: f.get('phone').trim(),
      email: emptyToNull(f.get('email').trim()),
      blood_group: emptyToNull(f.get('blood_group')),
      address: f.get('address').trim(),
    });
  };

  return (
    <form onSubmit={submit} className="form">
      <label>Full name<input name="full_name" required minLength={2} defaultValue={patient?.full_name} placeholder="e.g. Amit Kumar" /></label>
      <div className="form-row">
        <label>Date of birth<input type="date" name="date_of_birth" required defaultValue={patient?.date_of_birth} /></label>
        <label>
          Gender
          <select name="gender" defaultValue={patient?.gender ?? 'FEMALE'}>
            <option value="FEMALE">Female</option><option value="MALE">Male</option><option value="OTHER">Other</option>
          </select>
        </label>
      </div>
      <div className="form-row">
        <label>Phone<input name="phone" required defaultValue={patient?.phone} placeholder="+91 90000 00000" /></label>
        <label>
          Blood group
          <select name="blood_group" defaultValue={patient?.blood_group ?? ''}>
            <option value="">Unknown</option>
            {BLOOD_GROUPS.map((b) => <option key={b}>{b}</option>)}
          </select>
        </label>
      </div>
      <label>Email (optional)<input type="email" name="email" defaultValue={patient?.email ?? ''} /></label>
      <label>Address<textarea name="address" defaultValue={patient?.address ?? ''} /></label>
      <div className="form-actions">
        <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
        <button className="primary">{patient ? 'Save changes' : 'Register patient'}</button>
      </div>
    </form>
  );
}

function History({ patient }) {
  const { data, error, loading } = useLoader(() => api.patientHistory(patient.id), [patient.id]);
  if (loading) return <Empty>Loading history…</Empty>;
  if (error) return <ErrorBanner message={error} />;
  if (!data.length) return <Empty>No visits yet.</Empty>;
  return (
    <ul className="timeline">
      {data.map((a) => (
        <li key={a.id}>
          <span className="time">{formatDate(a.appointment_date)}<br />{formatTime(a.appointment_time)}</span>
          <div className="grow">
            <b>{a.doctor.full_name}</b>
            <small>{a.reason || a.doctor.specialization}{a.notes && ` · 📝 ${a.notes}`}</small>
          </div>
          <StatusBadge status={a.status} />
        </li>
      ))}
    </ul>
  );
}

export default function Patients({ notify }) {
  const [search, setSearch] = useState('');
  const { data, error, loading, reload } = useLoader(() => api.list('patients', { search }), [search]);
  const [editing, setEditing] = useState(null);
  const [history, setHistory] = useState(null);

  const save = async (payload) => {
    try {
      if (editing?.id) {
        await api.update('patients', editing.id, payload);
        notify('Patient updated');
      } else {
        await api.create('patients', payload);
        notify('Patient registered');
      }
      setEditing(null);
      reload();
    } catch (e) {
      notify(e.message, 'error');
    }
  };

  const remove = async (p) => {
    if (!window.confirm(`Delete ${p.full_name}? Their appointments will also be deleted.`)) return;
    try {
      await api.remove('patients', p.id);
      notify('Patient deleted');
      reload();
    } catch (e) {
      notify(e.message, 'error');
    }
  };

  return (
    <>
      <PageHeader eyebrow="CLINIC / PATIENTS" title="Patients" subtitle="Patient registry and visit history."
        action={<button className="primary" onClick={() => setEditing({})}>＋ Register patient</button>} />
      <ErrorBanner message={error} onRetry={reload} />

      <div className="panel">
        <div className="toolbar">
          <input type="search" className="search" placeholder="Search by name or phone…" value={search}
            onChange={(e) => setSearch(e.target.value)} aria-label="Search patients" />
          <span className="muted">{data?.length ?? 0} patients</span>
        </div>
        {loading && !data ? <Empty>Loading patients…</Empty> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Patient</th><th>Age / Gender</th><th>Phone</th><th>Blood</th><th>Address</th><th aria-label="Actions" /></tr></thead>
              <tbody>
                {data?.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <div className="person">
                        <span className="avatar small">{initials(p.full_name)}</span>
                        <div><b>{p.full_name}</b><small>{p.email || `#${p.id}`}</small></div>
                      </div>
                    </td>
                    <td>{age(p.date_of_birth)} yrs<small>{p.gender.charAt(0) + p.gender.slice(1).toLowerCase()}</small></td>
                    <td>{p.phone}</td>
                    <td>{p.blood_group ? <span className="blood">{p.blood_group}</span> : '—'}</td>
                    <td className="wrap">{p.address || '—'}</td>
                    <td className="actions">
                      <button className="icon-btn" title="Visit history" onClick={() => setHistory(p)}>🗂</button>
                      <button className="icon-btn" title="Edit" onClick={() => setEditing(p)}>✎</button>
                      <button className="icon-btn danger" title="Delete" onClick={() => remove(p)}>🗑</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!data?.length && <Empty>{search ? 'No patients match your search.' : 'No patients yet. Register the first one.'}</Empty>}
          </div>
        )}
      </div>

      {editing && (
        <Modal eyebrow={editing.id ? 'EDIT PATIENT' : 'NEW PATIENT'} title={editing.id ? editing.full_name : 'Register a patient'}
          onClose={() => setEditing(null)}>
          <PatientForm patient={editing.id ? editing : null} onSubmit={save} onCancel={() => setEditing(null)} />
        </Modal>
      )}
      {history && (
        <Modal eyebrow="VISIT HISTORY" title={history.full_name} onClose={() => setHistory(null)} wide>
          <History patient={history} />
        </Modal>
      )}
    </>
  );
}
