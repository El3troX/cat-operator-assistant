import { WifiOff } from 'lucide-react';
import { API_BASE_URL } from '../lib/api';
import { useLiveStatus } from '../lib/live';
import { useHealth } from '../lib/queries';
import { cn } from '../lib/utils';
import { Button } from './ui/button';
import { LiveDot } from './ui/live-dot';

export function ApiStatusPill({ className }) {
  const { isSuccess, isError } = useHealth();
  const { status } = useLiveStatus();
  const live = isSuccess && status === 'open';
  const label = live ? 'Live' : isSuccess ? 'Online' : isError ? 'Offline' : 'Connecting';
  return (
    <span
      className={cn('flex items-center gap-2 rounded-full border border-line bg-surface-2 px-3 py-1 text-xs font-semibold', className)}
      title={live ? `Live updates from ${API_BASE_URL}` : `Backend: ${API_BASE_URL}${isSuccess ? ' (live updates reconnecting)' : ''}`}
    >
      {isSuccess ? (
        <LiveDot />
      ) : (
        <span className={cn('size-2 rounded-full', isError ? 'bg-danger' : 'bg-warn animate-pulse')} aria-hidden />
      )}
      <span className={isError ? 'text-danger' : live ? 'text-ok' : 'text-muted'}>{label}</span>
    </span>
  );
}

export function ApiOfflineBanner() {
  const { isError, refetch, isFetching } = useHealth();
  if (!isError) return null;
  return (
    <div role="alert" className="mb-6 flex flex-col gap-3 rounded-xl border border-danger/40 bg-danger/10 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <WifiOff className="mt-0.5 size-5 shrink-0 text-danger" aria-hidden />
        <div>
          <p className="text-sm font-semibold text-ink">Can&apos;t reach the backend at {API_BASE_URL}</p>
          <p className="text-sm text-muted">
            Start it with <code className="rounded bg-surface-3 px-1.5 py-0.5 text-xs">cd backend &amp;&amp; uvicorn main:app --reload</code>
          </p>
        </div>
      </div>
      <Button size="sm" onClick={() => refetch()} loading={isFetching}>
        Retry
      </Button>
    </div>
  );
}
