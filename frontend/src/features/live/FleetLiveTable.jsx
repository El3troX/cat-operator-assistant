import { Activity, WifiOff } from 'lucide-react';
import { Card, CardBody, CardHeader } from '../../components/ui/card';
import { LiveDot } from '../../components/ui/live-dot';
import { IDLE_THRESHOLD_MIN, PROXIMITY_ALERT_M } from '../../lib/constants';
import { useFleetTelemetry } from '../../lib/live';
import { cn, formatDateTime } from '../../lib/utils';
import SeatbeltState from './SeatbeltState';

function nearestTone(m) {
  if (m <= PROXIMITY_ALERT_M) return 'text-danger';
  if (m <= 5) return 'text-warn';
  return 'text-ink';
}

export default function FleetLiveTable() {
  const frame = useFleetTelemetry();

  return (
    <Card>
      <CardHeader
        icon={Activity}
        title="Live fleet status"
        description="Cab readings replayed from the operation log, with simulated ground workers around each machine."
        action={
          frame ? (
            <span className="flex items-center gap-2 text-xs font-semibold text-ok">
              <LiveDot /> Streaming
            </span>
          ) : (
            <span className="flex items-center gap-2 text-xs font-semibold text-warn">
              <WifiOff className="size-3.5" aria-hidden /> Waiting for telemetry
            </span>
          )
        }
      />
      <CardBody>
        {frame ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-muted">
                <tr className="border-b border-line">
                  <th scope="col" className="py-2 pr-4 font-semibold">Machine</th>
                  <th scope="col" className="py-2 pr-4 font-semibold">Operator</th>
                  <th scope="col" className="py-2 pr-4 font-semibold">Seatbelt</th>
                  <th scope="col" className="py-2 pr-4 text-right font-semibold">Idle (min)</th>
                  <th scope="col" className="py-2 pr-4 text-right font-semibold">Fuel (L)</th>
                  <th scope="col" className="py-2 pr-4 text-right font-semibold">Load cycles</th>
                  <th scope="col" className="py-2 text-right font-semibold">Nearest person</th>
                </tr>
              </thead>
              <tbody className="tabular-nums">
                {frame.machines.map((m) => {
                  const idleOver = m.idling_time_min > IDLE_THRESHOLD_MIN;
                  return (
                    <tr key={m.machine_id} className="border-b border-line/60 last:border-0">
                      <td className="py-2.5 pr-4 font-semibold text-accent">{m.machine_id}</td>
                      <td className="py-2.5 pr-4 text-ink">{m.operator_id}</td>
                      <td className="py-2.5 pr-4">
                        <SeatbeltState status={m.seatbelt_status} />
                      </td>
                      <td className={cn('py-2.5 pr-4 text-right font-semibold', idleOver ? 'text-warn' : 'text-ink')}>
                        {m.idling_time_min ?? '—'}
                        {idleOver && <span className="sr-only"> (over {IDLE_THRESHOLD_MIN} min threshold)</span>}
                      </td>
                      <td className="py-2.5 pr-4 text-right text-ink">{m.fuel_used_l ?? '—'}</td>
                      <td className="py-2.5 pr-4 text-right text-ink">{m.load_cycles ?? '—'}</td>
                      <td className={cn('py-2.5 text-right font-bold', nearestTone(m.nearest_m))}>{m.nearest_m.toFixed(1)} m</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-3 text-xs text-faint">
              Replaying log readings from {formatDateTime(frame.machines[0]?.reading_ts)} · frame {formatDateTime(frame.ts)}
            </p>
          </div>
        ) : (
          <p className="text-sm text-muted">
            No live telemetry yet. It starts with the backend (SIM_ENABLED=true) once the operation log is seeded.
          </p>
        )}
      </CardBody>
    </Card>
  );
}
