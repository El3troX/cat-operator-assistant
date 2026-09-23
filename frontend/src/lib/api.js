export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, { method = 'GET', body, params } = {}) {
  const url = new URL(path, API_BASE_URL);
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== null && value !== undefined && value !== '') url.searchParams.set(key, value);
  }

  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      if (typeof data.detail === 'string') detail = data.detail;
      else if (Array.isArray(data.detail)) {
        // FastAPI 422 loc looks like ["body", "task_type"]; drop the "body"/"query" prefix.
        detail = data.detail.map((d) => (d.loc?.length > 1 ? `${d.loc.slice(1).join('.')}: ${d.msg}` : d.msg)).join('; ');
      }
      if (data.request_id) detail += ` (ref ${data.request_id})`;
    } catch {
      // non-JSON error body; keep statusText
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  health: () => request('/health'),

  tasksToday: () => request('/tasks/today'),
  updateTask: (id, patch) => request(`/tasks/${id}`, { method: 'PATCH', body: patch }),

  alerts: (machineId) => request('/safety/alerts', { params: { machine_id: machineId } }),
  safetyCheck: (payload) => request('/safety/check', { method: 'POST', body: payload }),
  proximity: (payload) => request('/safety/proximity', { method: 'POST', body: payload }),

  incidents: (machineId) => request('/incidents', { params: { machine_id: machineId } }),
  createIncident: (payload) => request('/incidents', { method: 'POST', body: payload }),

  anomalies: (machineId) => request('/anomalies', { params: { machine_id: machineId } }),

  predictTaskTime: (payload) => request('/predict/task-time', { method: 'POST', body: payload }),

  scores: (operatorId) => request('/scores/operators', { params: { operator_id: operatorId } }),

  trainingModules: () => request('/training/modules'),
  updateTrainingModule: (id, patch) =>
    request(`/training/modules/${id}`, { method: 'PATCH', body: patch }),
};
