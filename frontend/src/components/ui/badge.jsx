import { SEVERITY_META } from '../../lib/severity';
import { cn } from '../../lib/utils';

const TONES = {
  neutral: 'bg-surface-2 text-muted border-line',
  accent: 'bg-accent/12 text-accent border-accent/30',
  danger: 'bg-danger/12 text-danger border-danger/35',
  warn: 'bg-warn/12 text-warn border-warn/35',
  ok: 'bg-ok/12 text-ok border-ok/35',
  info: 'bg-info/12 text-info border-info/35',
};

export function Badge({ tone = 'neutral', className, children, ...props }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold whitespace-nowrap',
        TONES[tone],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}

// Severity always carries an icon + label, never color alone.
export function SeverityBadge({ severity, className }) {
  const meta = SEVERITY_META[severity] ?? SEVERITY_META.Low;
  const Icon = meta.icon;
  return (
    <Badge tone={meta.tone} className={cn('uppercase tracking-wide', className)}>
      <Icon className="size-3.5" aria-hidden />
      {severity ?? 'Info'}
    </Badge>
  );
}
