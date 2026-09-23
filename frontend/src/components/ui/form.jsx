import { useId } from 'react';
import { cn } from '../../lib/utils';

const CONTROL =
  'w-full rounded-lg border border-line bg-surface-2 px-3 text-sm text-ink placeholder:text-faint ' +
  'transition focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25';

export function Field({ label, hint, error, children, className }) {
  const id = useId();
  return (
    <div className={cn('space-y-1.5', className)}>
      <label htmlFor={id} className="block text-xs font-semibold uppercase tracking-wider text-muted">
        {label}
      </label>
      {children(id)}
      {error ? (
        <p role="alert" className="text-xs font-medium text-danger">
          {error}
        </p>
      ) : (
        hint && <p className="text-xs text-faint">{hint}</p>
      )}
    </div>
  );
}

export function Select({ options, className, size = 'md', ...props }) {
  return (
    <select className={cn(CONTROL, size === 'lg' ? 'h-14 text-base' : 'h-10', 'cursor-pointer', className)} {...props}>
      {options.map((opt) => {
        const value = typeof opt === 'string' ? opt : opt.value;
        const label = typeof opt === 'string' ? opt : opt.label;
        return (
          <option key={value} value={value} className="bg-surface-2">
            {label}
          </option>
        );
      })}
    </select>
  );
}

export function Input({ className, ...props }) {
  return <input className={cn(CONTROL, 'h-10', className)} {...props} />;
}

export function Textarea({ className, ...props }) {
  return <textarea className={cn(CONTROL, 'min-h-28 py-2.5 resize-y', className)} {...props} />;
}
