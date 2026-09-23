import { motion } from 'motion/react';
import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router';
import { ClipboardList, FileWarning, GraduationCap, LayoutDashboard, ShieldAlert } from 'lucide-react';
import { ApiOfflineBanner, ApiStatusPill } from '../components/ApiStatus';
import Brand from '../components/Brand';
import SessionPicker from '../components/SessionPicker';
import { cn } from '../lib/utils';

const TABS = [
  { to: '/cab', end: true, label: 'Tasks', icon: ClipboardList },
  { to: '/cab/safety', label: 'Safety', icon: ShieldAlert },
  { to: '/cab/report', label: 'Report', icon: FileWarning },
  { to: '/cab/training', label: 'Training', icon: GraduationCap },
];

function Clock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 15000);
    return () => clearInterval(id);
  }, []);
  return (
    <time className="text-2xl font-bold tabular-nums text-ink" dateTime={now.toISOString()}>
      {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
    </time>
  );
}

export default function CabLayout() {
  const location = useLocation();
  const currentTab = TABS.find((t) => (t.end ? location.pathname === t.to : location.pathname.startsWith(t.to))) ?? TABS[0];
  return (
    <div className="min-h-screen pb-28">
      <header className="sticky top-0 z-20 border-b border-line bg-canvas/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-4">
            <Brand subtitle="Cab Mode" />
            <Clock />
          </div>
          <div className="flex items-center gap-2">
            <SessionPicker large />
            <ApiStatusPill className="hidden sm:flex" />
            <NavLink
              to="/command"
              className="grid size-11 place-items-center rounded-lg border border-line bg-surface-2 text-muted transition hover:text-accent"
              aria-label="Switch to Command Center"
              title="Command Center"
            >
              <LayoutDashboard className="size-5" aria-hidden />
            </NavLink>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-6">
        <h1 className="sr-only">Cab Mode: {currentTab.label}</h1>
        <ApiOfflineBanner />
        <motion.div key={location.pathname} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
          <Outlet />
        </motion.div>
      </main>

      <nav
        className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface/95 backdrop-blur-md pb-[env(safe-area-inset-bottom)]"
        aria-label="Cab Mode"
      >
        <div className="mx-auto grid max-w-4xl grid-cols-4 gap-1 p-2">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  cn(
                    'relative flex h-16 flex-col items-center justify-center gap-1 rounded-xl text-sm font-semibold transition-colors',
                    isActive ? 'text-accent-ink' : 'text-muted hover:text-ink',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <motion.span
                        layoutId="cab-tab"
                        className="absolute inset-0 rounded-xl bg-accent"
                        transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                      />
                    )}
                    <Icon className="relative size-6" aria-hidden />
                    <span className="relative">{tab.label}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
