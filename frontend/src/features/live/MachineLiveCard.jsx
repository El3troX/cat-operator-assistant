import { Fuel, Repeat, Timer, UserRound } from 'lucide-react';
import { LiveDot } from '../../components/ui/live-dot';
import { IDLE_THRESHOLD_MIN } from '../../lib/constants';
import { useMachineTelemetry } from '../../lib/live';
import { useSession } from '../../lib/session';
import { cn } from '../../lib/utils';
import SeatbeltState from './SeatbeltState';

function Tile({ label, icon: Icon, children, className }) {
  return (
    <div className={cn('rounded-2xl border border-line bg-surface px-4 py-3', className)}>
      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted">
        {Icon && <Icon className="size-3.5" aria-hidden />}
        {label}
      </div>
      <div className="mt-1 text-2xl font-bold tabular-nums text-ink">{children}</div>
    </div>
  );
}

export default function MachineLiveCard() {
  const { machineId } = useSession();
  const reading = useMachineTelemetry(machineId);

  if (!reading) {
    return (
      <p className="rounded-2xl border border-dashed border-line px-4 py-3 text-sm text-muted">
        Live cab readings for {machineId} will appear here once telemetry is streaming.
      </p>
    );
  }

  const idleOver = reading.idling_time_min > IDLE_THRESHOLD_MIN;
  return (
    <section aria-label={`Live readings for ${machineId}`} className="space-y-2">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-ok">
        <LiveDot /> {machineId} live
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Tile label="Seatbelt" className={reading.seatbelt_status !== 'Fastened' && 'border-danger/50 bg-danger/8'}>
          <SeatbeltState status={reading.seatbelt_status} className="text-xl" />
        </Tile>
        <Tile label="Idle this hour" icon={Timer} className={idleOver && 'border-warn/50 bg-warn/8'}>
          <span className={idleOver ? 'text-warn' : undefined}>{reading.idling_time_min ?? '—'}</span>
          <span className="text-base font-medium text-muted"> min</span>
        </Tile>
        <Tile label="Fuel used" icon={Fuel}>
          {reading.fuel_used_l ?? '—'}
          <span className="text-base font-medium text-muted"> L</span>
        </Tile>
        <Tile label="Load cycles" icon={Repeat}>
          {reading.load_cycles ?? '—'}
        </Tile>
      </div>
      <p className="flex items-center gap-1.5 text-xs text-faint">
        <UserRound className="size-3" aria-hidden /> Logged operator {reading.operator_id} · replayed from the operation log
      </p>
    </section>
  );
}
