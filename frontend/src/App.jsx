import { useEffect, useState } from 'react';
import { checkHealth } from './api';
import Dashboard from './components/Dashboard';
import SafetyPanel from './components/SafetyPanel';
import TaskTimeEstimator from './components/TaskTimeEstimator';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [apiConnected, setApiConnected] = useState(null);

  useEffect(() => {
    const pingApi = async () => {
      try {
        await checkHealth();
        setApiConnected(true);
      } catch {
        setApiConnected(false);
      }
    };
    pingApi();
    const interval = setInterval(pingApi, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 sticky top-0 z-20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-amber-500 flex items-center justify-center font-black text-slate-950 text-base shadow">
              CAT
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white leading-tight">
                Smart Operator Assistant
              </h1>
              <p className="text-xs text-slate-400">Excavation & Telemetry Hub</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                apiConnected === true
                  ? 'bg-emerald-400 animate-pulse'
                  : apiConnected === false
                  ? 'bg-red-500'
                  : 'bg-amber-400'
              }`}
            />
            <span className="text-xs font-medium text-slate-400 hidden sm:inline">
              {apiConnected === true
                ? 'API Connected (8000)'
                : apiConnected === false
                ? 'API Offline'
                : 'Connecting...'}
            </span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`py-3 px-4 text-sm font-semibold border-b-2 transition whitespace-nowrap cursor-pointer ${
              activeTab === 'dashboard'
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            1. Daily Tasks Dashboard
          </button>
          <button
            onClick={() => setActiveTab('safety')}
            className={`py-3 px-4 text-sm font-semibold border-b-2 transition whitespace-nowrap cursor-pointer ${
              activeTab === 'safety'
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            2. Safety Alerts Panel
          </button>
          <button
            onClick={() => setActiveTab('estimator')}
            className={`py-3 px-4 text-sm font-semibold border-b-2 transition whitespace-nowrap cursor-pointer ${
              activeTab === 'estimator'
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            3. Task Time Estimator
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {apiConnected === false && (
          <div className="mb-6 p-4 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-sm flex items-center justify-between">
            <div>
              <strong>Cannot reach backend API at http://localhost:8000.</strong>
              <div className="text-xs text-red-400 mt-1">
                Start the backend with: <code>cd backend &amp;&amp; uvicorn main:app --reload</code>
              </div>
            </div>
            <button
              onClick={() => checkHealth().then(() => setApiConnected(true)).catch(() => setApiConnected(false))}
              className="px-3 py-1 bg-red-900/60 hover:bg-red-900 text-red-200 text-xs font-semibold rounded border border-red-700 transition"
            >
              Retry
            </button>
          </div>
        )}

        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'safety' && <SafetyPanel />}
        {activeTab === 'estimator' && <TaskTimeEstimator />}
      </main>

      {/* Minimal Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500">
        CAT Machinery Smart Operator Assistant · Hackathon Build · React + Vite + Tailwind
      </footer>
    </div>
  );
}
