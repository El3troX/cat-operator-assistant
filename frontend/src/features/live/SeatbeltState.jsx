import { ShieldAlert, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';

export default function SeatbeltState({ status, className }) {
  const fastened = status === 'Fastened';
  const Icon = fastened ? ShieldCheck : ShieldAlert;
  return (
    <span className={cn('inline-flex items-center gap-1.5 font-semibold', fastened ? 'text-ok' : 'text-danger', className)}>
      <Icon className="size-4" aria-hidden />
      {status ?? 'Unknown'}
    </span>
  );
}
