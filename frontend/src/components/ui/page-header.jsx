export function PageHeader({ title, description, actions }) {
  return (
    <div className="flex flex-col gap-4 pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function StatTile({ label, value, icon: Icon, tone = 'text-ink', hint }) {
  return (
    <div className="rounded-2xl border border-line bg-surface px-4 py-3.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted">{label}</span>
        {Icon && <Icon className={`size-4 ${tone}`} aria-hidden />}
      </div>
      <div className={`mt-1.5 text-3xl font-bold tabular-nums ${tone}`}>{value}</div>
      {hint && <div className="mt-0.5 text-xs text-faint">{hint}</div>}
    </div>
  );
}
