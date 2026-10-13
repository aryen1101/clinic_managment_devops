import { useState } from 'react';
import { api } from '../api.js';
import { Empty, ErrorBanner, PageHeader } from '../components/Common.jsx';
import Modal from '../components/Modal.jsx';
import { initials, useLoader } from '../utils.js';

function DoctorForm({ doctor, onSubmit, onCancel }) {
  const submit = (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    onSubmit({
      full_name: f.get('full_name').trim(),
      specialization: f.get('specialization').trim(),
      phone: f.get('phone').trim(),
      email: f.get('email').trim(),
      consultation_fee: Number(f.get('consultation_fee')),
      is_available: f.get('is_available') === 'on',
    });
  };

  return (
    <form onSubmit={submit} className="form">
      <label>Full name<input name="full_name" required minLength={2} defaultValue={doctor?.full_name} placeholder="Dr. Ananya Sharma" /></label>
      <div className="form-row">
        <label>Specialization<input name="specialization" required list="specializations" defaultValue={doctor?.specialization} /></label>
        <label>Fee (₹)<input type="number" name="consultation_fee" min="0" required defaultValue={doctor?.consultation_fee ?? 500} /></label>
      </div>
      <datalist id="specializations">
        {['General Medicine', 'Cardiology', 'Orthopedics', 'Pediatrics', 'Dermatology', 'Neurology', 'ENT', 'Gynecology']
          .map((s) => <option key={s} value={s} />)}
      </datalist>
      <div className="form-row">
        <label>Phone<input name="phone" required defaultValue={doctor?.phone} /></label>
        <label>Email<input type="email" name="email" required defaultValue={doctor?.email} /></label>
      </div>
      <label className="checkbox">
        <input type="checkbox" name="is_available" defaultChecked={doctor?.is_available ?? true} /> Available for appointments
      </label>
      <div className="form-actions">
        <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
        <button className="primary">{doctor ? 'Save changes' : 'Add doctor'}</button>
      </div>
    </form>
  );
}

export default function Doctors({ notify }) {
  const [specialization, setSpecialization] = useState('');
  const { data, error, loading, reload } = useLoader(() => api.list('doctors', { specialization }), [specialization]);
  const [editing, setEditing] = useState(null);

  const save = async (payload) => {
    try {
      if (editing?.id) {
        await api.update('doctors', editing.id, payload);
        notify('Doctor updated');
      } else {
        await api.create('doctors', payload);
        notify('Doctor added');
      }
      setEditing(null);
      reload();
    } catch (e) {
      notify(e.message, 'error');
    }
  };

  const toggle = async (d) => {
    try {
      await api.update('doctors', d.id, { is_available: !d.is_available });
      notify(`${d.full_name} is now ${d.is_available ? 'unavailable' : 'available'}`);
      reload();
    } catch (e) {
      notify(e.message, 'error');
    }
  };

  const remove = async (d) => {
    if (!window.confirm(`Delete ${d.full_name}? Their appointments will also be deleted.`)) return;
    try {
      await api.remove('doctors', d.id);
      notify('Doctor deleted');
      reload();
    } catch (e) {
      notify(e.message, 'error');
    }
  };

  return (
    <>
      <PageHeader eyebrow="CLINIC / DOCTORS" title="Doctors" subtitle="Medical staff, specializations and availability."
        action={<button className="primary" onClick={() => setEditing({})}>＋ Add doctor</button>} />
      <ErrorBanner message={error} onRetry={reload} />

      <div className="toolbar standalone">
        <input type="search" className="search" placeholder="Filter by specialization…" value={specialization}
          onChange={(e) => setSpecialization(e.target.value)} aria-label="Filter doctors" />
      </div>

      {loading && !data ? <Empty>Loading doctors…</Empty> : !data?.length ? (
        <div className="panel"><Empty>No doctors found.</Empty></div>
      ) : (
        <section className="card-grid">
          {data.map((d) => (
            <article className="panel doctor" key={d.id}>
              <div className="doctor-head">
                <span className="avatar">{initials(d.full_name)}</span>
                <div className="grow">
                  <b>{d.full_name}</b>
                  <span className="tag">{d.specialization}</span>
                </div>
              </div>
              <dl>
                <div><dt>Fee</dt><dd>₹{d.consultation_fee}</dd></div>
                <div><dt>Phone</dt><dd>{d.phone}</dd></div>
                <div><dt>Email</dt><dd className="ellipsis">{d.email}</dd></div>
              </dl>
              <div className="doctor-foot">
                <button className={`switch ${d.is_available ? 'on' : ''}`} onClick={() => toggle(d)}
                  role="switch" aria-checked={d.is_available}>
                  <i /> {d.is_available ? 'Available' : 'Unavailable'}
                </button>
                <div className="actions">
                  <button className="icon-btn" title="Edit" onClick={() => setEditing(d)}>✎</button>
                  <button className="icon-btn danger" title="Delete" onClick={() => remove(d)}>🗑</button>
                </div>
              </div>
            </article>
          ))}
        </section>
      )}

      {editing && (
        <Modal eyebrow={editing.id ? 'EDIT DOCTOR' : 'NEW DOCTOR'} title={editing.id ? editing.full_name : 'Add a doctor'}
          onClose={() => setEditing(null)}>
          <DoctorForm doctor={editing.id ? editing : null} onSubmit={save} onCancel={() => setEditing(null)} />
        </Modal>
      )}
    </>
  );
}
