import { cn } from '../../lib/utils';

export function LiveDot({ className, tone = 'bg-ok' }) {
  return (
    <span className={cn('relative flex size-2', className)} aria-hidden>
      <span className={cn('absolute inline-flex size-full animate-ping rounded-full opacity-60', tone)} />
      <span className={cn('relative inline-flex size-2 rounded-full', tone)} />
    </span>
  );
}
