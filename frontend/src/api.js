const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function checkHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) throw new Error('API server unreachable');
  return res.json();
}

export async function fetchTasksToday() {
  const res = await fetch(`${API_BASE_URL}/tasks/today`);
  if (!res.ok) throw new Error(`Failed to fetch tasks: ${res.statusText}`);
  return res.json();
}

export async function updateTask(id, patchData) {
  const res = await fetch(`${API_BASE_URL}/tasks/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(patchData),
  });
  if (!res.ok) throw new Error(`Failed to update task: ${res.statusText}`);
  return res.json();
}

export async function fetchAlerts(machineId = null) {
  const url = machineId
    ? `${API_BASE_URL}/safety/alerts?machine_id=${encodeURIComponent(machineId)}`
    : `${API_BASE_URL}/safety/alerts`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.statusText}`);
  return res.json();
}

export async function predictTaskTime(payload) {
  const res = await fetch(`${API_BASE_URL}/predict/task-time`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to predict task time: ${res.statusText}`);
  return res.json();
}
