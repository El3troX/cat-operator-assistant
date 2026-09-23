import { cn } from '../../lib/utils';

export function Card({ className, ...props }) {
  return <div className={cn('rounded-2xl border border-line bg-surface', className)} {...props} />;
}

export function CardHeader({ title, description, icon: Icon, action, className }) {
  return (
    <div className={cn('flex flex-wrap items-start justify-between gap-x-4 gap-y-3 px-5 pt-5', className)}>
      <div className="flex items-start gap-3 min-w-0">
        {Icon && (
          <div className="mt-0.5 grid size-9 shrink-0 place-items-center rounded-lg bg-surface-2 text-accent">
            <Icon className="size-[18px]" aria-hidden />
          </div>
        )}
        <div className="min-w-0">
          <h3 className="text-[15px] font-semibold text-ink leading-tight">{title}</h3>
          {description && <p className="mt-1 text-sm text-muted">{description}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

export function CardBody({ className, ...props }) {
  return <div className={cn('p-5', className)} {...props} />;
}
