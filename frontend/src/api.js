// Small wrapper around fetch. The browser only ever calls relative URLs (/api/...);
// nginx (Docker) or the Ingress (Kubernetes) routes them to the backend.
const BASE = '/api';

function errorMessage(status, data) {
  if (!data?.detail) return `Request failed (${status})`;
  if (typeof data.detail === 'string') return data.detail;
  // FastAPI validation errors: [{loc: [...], msg: '...'}]
  return data.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join(', ');
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(errorMessage(res.status, data));
  return data;
}

function query(params = {}) {
  const clean = Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined);
  const qs = new URLSearchParams(clean).toString();
  return qs ? `?${qs}` : '';
}

export const api = {
  stats: () => request('/stats'),
  list: (resource, params) => request(`/${resource}${query(params)}`),
  create: (resource, body) => request(`/${resource}`, { method: 'POST', body: JSON.stringify(body) }),
  update: (resource, id, body) => request(`/${resource}/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  remove: (resource, id) => request(`/${resource}/${id}`, { method: 'DELETE' }),
  patientHistory: (id) => request(`/patients/${id}/appointments`),
};

export async function systemStatus() {
  const check = async (url) => {
    try {
      const res = await fetch(url);
      return res.ok;
    } catch {
      return false;
    }
  };
  const [api, db] = await Promise.all([check('/health'), check('/ready')]);
  return { api, db };
}
