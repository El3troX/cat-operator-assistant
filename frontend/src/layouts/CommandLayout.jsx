import { motion } from 'motion/react';
import { NavLink, Outlet, useLocation } from 'react-router';
import { Activity, ArrowLeftRight, Calculator, ClipboardList, FileWarning, GraduationCap, ShieldAlert } from 'lucide-react';
import { ApiOfflineBanner, ApiStatusPill } from '../components/ApiStatus';
import Brand from '../components/Brand';
import LiveAlertToaster from '../components/LiveAlertToaster';
import SessionPicker from '../components/SessionPicker';
import { cn } from '../lib/utils';

const NAV = [
  { to: '/command', end: true, label: 'Daily tasks', icon: ClipboardList },
  { to: '/command/safety', label: 'Safety', icon: ShieldAlert },
  { to: '/command/incidents', label: 'Incidents', icon: FileWarning },
  { to: '/command/anomalies', label: 'Unusual behaviour', icon: Activity },
  { to: '/command/training', label: 'Training hub', icon: GraduationCap },
  { to: '/command/estimator', label: 'Time estimator', icon: Calculator },
];

function NavItem({ item, compact }) {
  const Icon = item.icon;
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        cn(
          'relative flex items-center gap-3 rounded-lg font-medium whitespace-nowrap transition-colors',
          compact ? 'px-3 py-2 text-xs' : 'px-3 py-2.5 text-sm',
          isActive ? 'text-ink' : 'text-muted hover:bg-surface-2 hover:text-ink',
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <motion.span
              layoutId={compact ? 'nav-active-compact' : 'nav-active'}
              className="absolute inset-0 rounded-lg border border-line-strong bg-surface-2"
              transition={{ type: 'spring', stiffness: 500, damping: 40 }}
            />
          )}
          <Icon className={cn('relative size-4', isActive && 'text-accent')} aria-hidden />
          <span className="relative">{item.label}</span>
        </>
      )}
    </NavLink>
  );
}

export default function CommandLayout() {
  const location = useLocation();
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <LiveAlertToaster />
      <aside className="sticky top-0 hidden h-screen flex-col border-r border-line bg-surface/60 p-4 lg:flex">
        <Brand subtitle="Command Center" />
        <nav className="mt-8 flex flex-col gap-1" aria-label="Command Center">
          {NAV.map((item) => (
            <NavItem key={item.to} item={item} />
          ))}
        </nav>
        <NavLink
          to="/cab"
          className="mt-auto flex items-center justify-between rounded-xl border border-accent/30 bg-accent/8 px-4 py-3 text-sm font-semibold text-accent transition hover:bg-accent/14"
        >
          Switch to Cab Mode <ArrowLeftRight className="size-4" aria-hidden />
        </NavLink>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-20 border-b border-line bg-canvas/80 backdrop-blur-md">
          <div className="flex items-center justify-between gap-3 px-4 py-3 sm:px-6">
            <div className="lg:hidden">
              <Brand />
            </div>
            <div className="hidden text-sm text-muted lg:block">Fleet overview · 5 machines · 10 operators</div>
            <div className="flex items-center gap-2">
              <div className="hidden sm:block">
                <SessionPicker />
              </div>
              <ApiStatusPill />
              <NavLink to="/cab" className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-accent lg:hidden">
                Cab
              </NavLink>
            </div>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-3 pb-2 [scrollbar-width:none] lg:hidden" aria-label="Command Center sections">
            {NAV.map((item) => (
              <NavItem key={item.to} item={item} compact />
            ))}
          </nav>
        </header>

        {/* Motion layout animations briefly scale rows when the width changes (e.g. a scrollbar appears); clip that overshoot. */}
        <main className="mx-auto max-w-7xl overflow-x-clip px-4 py-8 sm:px-6">
          <ApiOfflineBanner />
          <motion.div key={location.pathname} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  );
}
