import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';
import { Radio, ShieldAlert, ShieldCheck, Timer } from 'lucide-react';
import { toast } from 'sonner';
import { SeverityBadge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardBody, CardHeader } from '../../components/ui/card';
import { Segmented } from '../../components/ui/segmented';
import { IDLE_THRESHOLD_MIN } from '../../lib/constants';
import { useMachineTelemetry } from '../../lib/live';
import { markLocalAlerts } from '../../lib/local-alerts';
import { useSafetyCheck } from '../../lib/queries';
import { useSession } from '../../lib/session';
import { buzz, cn, nowLocalIso } from '../../lib/utils';

const SEATBELT_OPTIONS = [
  { value: 'Fastened', label: 'Fastened', icon: ShieldCheck, activeBg: 'bg-ok', activeClass: 'text-canvas' },
  { value: 'Unfastened', label: 'Unfastened', icon: ShieldAlert, activeBg: 'bg-danger', activeClass: 'text-white' },
];

export default function SafetyCheck({ size = 'md' }) {
  const { machineId, operatorId } = useSession();
  const liveReading = useMachineTelemetry(machineId);
  const check = useSafetyCheck();
  const [seatbelt, setSeatbelt] = useState('Fastened');
  const [idle, setIdle] = useState(20);
  const overIdle = idle > IDLE_THRESHOLD_MIN;
  const lg = size === 'lg';

  const run = () => {
    const timestamp = nowLocalIso();
    markLocalAlerts(['Seatbelt', 'Idling'], machineId, timestamp);
    check.mutate(
      {
        machine_id: machineId,
        operator_id: operatorId,
        seatbelt_status: seatbelt,
        idling_time_min: idle,
        timestamp,
      },
      {
        onSuccess: (alerts) => {
          if (alerts.length) {
            buzz();
            toast.warning(`${alerts.length} safety alert${alerts.length > 1 ? 's' : ''} raised`, {
              description: alerts.map((a) => a.message).join(' · '),
            });
          } else {
            toast.success('All clear', { description: 'No rules triggered for this reading.' });
          }
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader
        icon={ShieldCheck}
        title="Live safety check"
        description={`Run the rule engine on the current cab reading for ${machineId} / ${operatorId}.`}
        action={
          liveReading && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setSeatbelt(liveReading.seatbelt_status === 'Unfastened' ? 'Unfastened' : 'Fastened');
                setIdle(liveReading.idling_time_min ?? 0);
              }}
            >
              <Radio className="size-3.5" aria-hidden /> Use live reading
            </Button>
          )
        }
      />
      <CardBody className="space-y-5">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">Seatbelt</div>
          <Segmented
            label="Seatbelt status"
            value={seatbelt}
            onChange={setSeatbelt}
            options={SEATBELT_OPTIONS}
            size={lg ? 'lg' : 'md'}
            className="w-full"
          />
        </div>

        <label className="block">
          <div className="mb-2 flex items-baseline justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted">Idling this hour</span>
            <span className={cn('flex items-center gap-1 font-bold tabular-nums', lg ? 'text-2xl' : 'text-lg', overIdle ? 'text-warn' : 'text-ink')}>
              <Timer className="size-4" aria-hidden />
              {idle} min
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={90}
            value={idle}
            onChange={(e) => setIdle(Number(e.target.value))}
            className="w-full accent-[var(--color-accent)]"
          />
          <div className="mt-1 flex justify-between text-xs text-faint">
            <span>0</span>
            <span className={overIdle ? 'text-warn font-semibold' : undefined}>Threshold {IDLE_THRESHOLD_MIN} min</span>
            <span>90</span>
          </div>
        </label>

        <Button variant="primary" size={lg ? 'xl' : 'lg'} className="w-full" onClick={run} loading={check.isPending}>
          Run safety check
        </Button>

        <AnimatePresence mode="wait">
          {check.data && (
            <motion.div
              key={check.submittedAt}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              role="status"
            >
              {check.data.length === 0 ? (
                <div className="flex items-center gap-2 rounded-xl border border-ok/30 bg-ok/8 px-4 py-3 text-sm font-semibold text-ok">
                  <ShieldCheck className="size-4" aria-hidden /> All clear. No rules triggered.
                </div>
              ) : (
                <ul className="space-y-2">
                  {check.data.map((a) => (
                    <li key={a.id} className="flex items-center justify-between gap-3 rounded-xl border border-line bg-surface-2 px-4 py-3">
                      <span className="text-sm font-medium text-ink">{a.message}</span>
                      <SeverityBadge severity={a.severity} />
                    </li>
                  ))}
                </ul>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </CardBody>
    </Card>
  );
}
