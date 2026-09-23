import { CircleCheck, RefreshCw, WifiOff } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from './button';

export function Skeleton({ className }) {
  return <div className={cn('animate-pulse rounded-lg bg-surface-2', className)} />;
}

export function SkeletonList({ rows = 4, className }) {
  return (
    <div className={cn('space-y-2.5', className)} aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} className="h-16" />
      ))}
    </div>
  );
}

export function EmptyState({ icon: Icon = CircleCheck, title, description, className }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-line px-6 py-10 text-center',
        className,
      )}
    >
      <Icon className="size-7 text-faint" aria-hidden />
      <p className="text-sm font-semibold text-ink">{title}</p>
      {description && <p className="max-w-sm text-sm text-muted">{description}</p>}
    </div>
  );
}

export function ErrorState({ error, onRetry, className }) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col gap-3 rounded-xl border border-danger/35 bg-danger/8 px-5 py-4 sm:flex-row sm:items-center sm:justify-between',
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <WifiOff className="mt-0.5 size-5 shrink-0 text-danger" aria-hidden />
        <div>
          <p className="text-sm font-semibold text-ink">Couldn&apos;t load data</p>
          <p className="text-sm text-muted">{error?.message ?? 'Unknown error'}</p>
        </div>
      </div>
      {onRetry && (
        <Button size="sm" onClick={onRetry}>
          <RefreshCw className="size-3.5" aria-hidden /> Retry
        </Button>
      )}
    </div>
  );
}
