import { useEffect, useState } from 'react';
import { fetchTasksToday, updateTask } from '../api';

const STATUS_OPTIONS = ['Pending', 'In Progress', 'Completed'];

export default function Dashboard() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);

  const loadTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchTasksToday();
      setTasks(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      setUpdatingId(taskId);
      const updated = await updateTask(taskId, { status: newStatus });
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: updated.status } : t))
      );
    } catch (err) {
      alert(`Failed to update task: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-700">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Daily Machinery Tasks</h2>
          <p className="text-sm text-slate-400 mt-1">
            Real-time schedule for active excavators and operators
          </p>
        </div>
        <button
          onClick={loadTasks}
          className="self-start sm:self-auto px-3.5 py-1.5 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-md transition"
        >
          Refresh Tasks
        </button>
      </div>

      {loading && (
        <div className="p-8 text-center text-slate-400 animate-pulse">
          Loading tasks from backend...
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-sm">
          <strong>Error loading tasks:</strong> {error}
          <div className="mt-2 text-xs text-red-400">
            Ensure backend server is active at <code>http://localhost:8000</code>.
          </div>
        </div>
      )}

      {!loading && !error && tasks.length === 0 && (
        <div className="p-8 text-center text-slate-400 border border-dashed border-slate-700 rounded-lg">
          No tasks found for today.
        </div>
      )}

      {!loading && !error && tasks.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="bg-slate-800/80 border border-slate-700 rounded-lg p-5 shadow-sm hover:border-slate-600 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-0.5 text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded">
                    {task.machine_id}
                  </span>
                  <span className="text-xs text-slate-400">
                    Op: <strong className="text-slate-200">{task.operator_id}</strong>
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-white mb-2">
                  {task.task_type}
                </h3>

                <div className="space-y-1.5 text-sm text-slate-300 mb-4">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Estimated:</span>
                    <span className="font-medium text-slate-200">
                      {task.estimated_time_min ? `${task.estimated_time_min} min` : 'N/A'}
                    </span>
                  </div>

                  {task.actual_time_min !== null && task.actual_time_min !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Actual:</span>
                      <span className="font-medium text-emerald-400">
                        {task.actual_time_min} min
                      </span>
                    </div>
                  )}

                  {task.scheduled_time && (
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Scheduled:</span>
                      <span>{new Date(task.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-700/60 flex items-center justify-between">
                <label className="text-xs font-medium text-slate-400">Status:</label>
                <div className="relative">
                  <select
                    value={task.status}
                    disabled={updatingId === task.id}
                    onChange={(e) => handleStatusChange(task.id, e.target.value)}
                    className={`text-xs font-medium rounded px-2.5 py-1.5 border transition cursor-pointer ${
                      task.status === 'Completed'
                        ? 'bg-emerald-950/50 text-emerald-300 border-emerald-700'
                        : task.status === 'In Progress'
                        ? 'bg-blue-950/50 text-blue-300 border-blue-700'
                        : 'bg-slate-700 text-slate-200 border-slate-600'
                    } disabled:opacity-50`}
                  >
                    {STATUS_OPTIONS.map((opt) => (
                      <option key={opt} value={opt} className="bg-slate-800 text-slate-200">
                        {opt}
                      </option>
                    ))}
                  </select>
                  {updatingId === task.id && (
                    <span className="absolute -top-6 right-0 text-[10px] text-amber-400">
                      Saving...
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
