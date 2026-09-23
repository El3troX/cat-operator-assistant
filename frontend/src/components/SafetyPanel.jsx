import { useEffect, useState } from 'react';
import { fetchAlerts } from '../api';

const MACHINES = ['All', 'EXC001', 'EXC002', 'EXC003', 'EXC004', 'EXC005'];

export default function SafetyPanel() {
  const [alerts, setAlerts] = useState([]);
  const [selectedMachine, setSelectedMachine] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAlerts = async (machine) => {
    try {
      setLoading(true);
      setError(null);
      const machineParam = machine === 'All' ? null : machine;
      const data = await fetchAlerts(machineParam);
      setAlerts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts(selectedMachine);
  }, [selectedMachine]);

  const getSeverityStyle = (severity) => {
    const sev = (severity || '').toLowerCase();
    if (sev === 'high') {
      return {
        cardBorder: 'border-l-red-500 bg-red-950/20 border-slate-700 hover:border-slate-600',
        badge: 'bg-red-500/20 text-red-300 border-red-500/30',
        text: 'text-red-400',
      };
    }
    if (sev === 'medium') {
      return {
        cardBorder: 'border-l-amber-500 bg-amber-950/20 border-slate-700 hover:border-slate-600',
        badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        text: 'text-amber-400',
      };
    }
    return {
      cardBorder: 'border-l-emerald-500 bg-emerald-950/20 border-slate-700 hover:border-slate-600',
      badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      text: 'text-emerald-400',
    };
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-700">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Safety & Anomaly Alerts</h2>
          <p className="text-sm text-slate-400 mt-1">
            Real-time telemetry and rule-engine alerts (Seatbelt, Proximity, Idling)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-medium">Filter Machine:</label>
          <select
            value={selectedMachine}
            onChange={(e) => setSelectedMachine(e.target.value)}
            className="bg-slate-800 text-slate-200 text-sm border border-slate-700 rounded-md px-3 py-1.5 focus:outline-none focus:border-slate-500"
          >
            {MACHINES.map((m) => (
              <option key={m} value={m}>
                {m === 'All' ? 'All Machines' : m}
              </option>
            ))}
          </select>
          <button
            onClick={() => loadAlerts(selectedMachine)}
            className="px-3.5 py-1.5 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-md transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {loading && (
        <div className="p-8 text-center text-slate-400 animate-pulse">
          Loading safety alerts...
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-sm">
          <strong>Error loading alerts:</strong> {error}
        </div>
      )}

      {!loading && !error && alerts.length === 0 && (
        <div className="p-8 text-center text-slate-400 border border-dashed border-slate-700 rounded-lg">
          No safety alerts found.
        </div>
      )}

      {!loading && !error && alerts.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs text-slate-400">
            Showing <strong className="text-slate-200">{alerts.length}</strong> alerts
          </div>

          <div className="space-y-2.5">
            {alerts.map((alert) => {
              const styles = getSeverityStyle(alert.severity);
              return (
                <div
                  key={alert.id}
                  className={`p-4 rounded-lg border border-l-4 ${styles.cardBorder} transition flex flex-col sm:flex-row sm:items-center justify-between gap-3`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`px-2 py-0.5 text-xs font-bold uppercase rounded border ${styles.badge}`}>
                        {alert.severity || 'Info'}
                      </span>
                      <span className="px-2 py-0.5 text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700 rounded">
                        {alert.type}
                      </span>
                      <span className="text-xs font-semibold text-amber-400">
                        {alert.machine_id}
                      </span>
                      {alert.operator_id && alert.operator_id !== 'SYSTEM' && (
                        <span className="text-xs text-slate-400">
                          ({alert.operator_id})
                        </span>
                      )}
                    </div>
                    <div className="text-sm font-medium text-slate-100 pt-0.5">
                      {alert.message}
                    </div>
                  </div>

                  <div className="text-xs text-slate-400 shrink-0 sm:text-right">
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Just now'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
