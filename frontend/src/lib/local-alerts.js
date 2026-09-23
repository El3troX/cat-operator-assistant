// Alerts raised by an action in this tab already get feedback from that action,
// so the live feed only toasts alerts that arrive from elsewhere (another cab, another screen).
const localKeys = new Set();

const keyOf = (type, machineId, timestamp) => `${type}|${machineId}|${timestamp}`;

export function markLocalAlerts(types, machineId, timestamp) {
  for (const type of types) localKeys.add(keyOf(type, machineId, timestamp));
}

export function isLocalAlert(alert) {
  return localKeys.has(keyOf(alert.type, alert.machine_id, alert.timestamp));
}
