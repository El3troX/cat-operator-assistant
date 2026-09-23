import { useState } from 'react';
import { predictTaskTime } from '../api';

const TASK_TYPES = [
  'Earth Excavation',
  'Trenching',
  'Material Loading',
  'Grading',
  'Demolition',
];

const WEATHERS = ['Sunny', 'Rainy', 'Cloudy', 'Windy'];
const OPERATOR_SKILLS = ['Beginner', 'Intermediate', 'Expert'];
const MACHINE_AGES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

export default function TaskTimeEstimator() {
  const [taskType, setTaskType] = useState('Trenching');
  const [weather, setWeather] = useState('Rainy');
  const [operatorSkill, setOperatorSkill] = useState('Intermediate');
  const [machineAgeYrs, setMachineAgeYrs] = useState(4);

  const [predictedMinutes, setPredictedMinutes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const payload = {
        task_type: taskType,
        weather: weather,
        operator_skill: operatorSkill,
        machine_age_yrs: Number(machineAgeYrs),
      };
      const res = await predictTaskTime(payload);
      setPredictedMinutes(res.predicted_minutes);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="pb-4 border-b border-slate-700">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          Task Completion Time Estimator
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          ML Random Forest regression model estimating actual operation duration
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-slate-800/80 border border-slate-700 rounded-lg p-6 space-y-5 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Task Type
            </label>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="w-full bg-slate-900 text-slate-100 border border-slate-700 rounded-md px-3.5 py-2 text-sm focus:outline-none focus:border-amber-500 transition"
            >
              {TASK_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Weather Condition
            </label>
            <select
              value={weather}
              onChange={(e) => setWeather(e.target.value)}
              className="w-full bg-slate-900 text-slate-100 border border-slate-700 rounded-md px-3.5 py-2 text-sm focus:outline-none focus:border-amber-500 transition"
            >
              {WEATHERS.map((w) => (
                <option key={w} value={w}>
                  {w}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Operator Skill Level
            </label>
            <select
              value={operatorSkill}
              onChange={(e) => setOperatorSkill(e.target.value)}
              className="w-full bg-slate-900 text-slate-100 border border-slate-700 rounded-md px-3.5 py-2 text-sm focus:outline-none focus:border-amber-500 transition"
            >
              {OPERATOR_SKILLS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Machine Age (Years)
            </label>
            <select
              value={machineAgeYrs}
              onChange={(e) => setMachineAgeYrs(Number(e.target.value))}
              className="w-full bg-slate-900 text-slate-100 border border-slate-700 rounded-md px-3.5 py-2 text-sm focus:outline-none focus:border-amber-500 transition"
            >
              {MACHINE_AGES.map((age) => (
                <option key={age} value={age}>
                  {age} {age === 1 ? 'year' : 'years'} old
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 px-4 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-md transition shadow flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
        >
          {loading ? 'Running ML Inference...' : 'Predict Duration'}
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-sm">
          <strong>Prediction Failed:</strong> {error}
        </div>
      )}

      {predictedMinutes !== null && (
        <div className="bg-emerald-950/30 border border-emerald-800 rounded-lg p-6 text-center shadow">
          <div className="text-xs uppercase tracking-wider font-semibold text-emerald-400 mb-1">
            Predicted Operation Time
          </div>
          <div className="text-5xl font-black text-emerald-300 my-2">
            {predictedMinutes} <span className="text-2xl font-medium text-emerald-400">min</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Calculated for <strong className="text-slate-200">{taskType}</strong> under{' '}
            <strong className="text-slate-200">{weather}</strong> conditions with a{' '}
            <strong className="text-slate-200">{operatorSkill}</strong> operator ({machineAgeYrs} yr old machine).
          </p>
        </div>
      )}
    </div>
  );
}
