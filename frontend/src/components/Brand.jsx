import { HardHat } from 'lucide-react';

export default function Brand({ subtitle }) {
  return (
    <div className="flex items-center gap-3">
      <div className="grid size-9 place-items-center rounded-xl bg-accent text-accent-ink shadow-[0_0_24px_-6px_var(--color-accent)]">
        <HardHat className="size-5" aria-hidden />
      </div>
      <div className="leading-tight">
        <div className="text-sm font-bold tracking-tight text-ink">Operator Assist</div>
        {subtitle && <div className="text-xs text-muted">{subtitle}</div>}
      </div>
    </div>
  );
}
