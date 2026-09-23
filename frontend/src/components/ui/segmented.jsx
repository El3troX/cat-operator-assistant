import { motion } from 'motion/react';
import { useId } from 'react';
import { cn } from '../../lib/utils';

// Radio-group style toggle with a sliding highlight.
export function Segmented({ value, onChange, options, size = 'md', label, className }) {
  const layoutId = useId();
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={cn('inline-flex rounded-xl border border-line bg-surface-2 p-1', className)}
    >
      {options.map((opt) => {
        const optValue = typeof opt === 'string' ? opt : opt.value;
        const optLabel = typeof opt === 'string' ? opt : opt.label;
        const Icon = typeof opt === 'string' ? null : opt.icon;
        const active = optValue === value;
        return (
          <button
            key={optValue}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(optValue)}
            className={cn(
              'relative flex flex-1 items-center justify-center rounded-lg font-semibold whitespace-nowrap cursor-pointer transition-colors',
              size === 'lg' ? 'h-14 gap-1.5 px-2.5 text-base sm:gap-2 sm:px-5' : 'h-8 gap-2 px-3 text-xs',
              active ? (opt.activeClass ?? 'text-accent-ink') : 'text-muted hover:text-ink',
            )}
          >
            {active && (
              <motion.span
                layoutId={layoutId}
                className={cn('absolute inset-0 rounded-lg', opt.activeBg ?? 'bg-accent')}
                transition={{ type: 'spring', stiffness: 500, damping: 38 }}
              />
            )}
            <span className="relative flex items-center gap-[inherit]">
              {Icon && <Icon className={size === 'lg' ? 'size-5' : 'size-3.5'} aria-hidden />}
              {optLabel}
            </span>
          </button>
        );
      })}
    </div>
  );
}
