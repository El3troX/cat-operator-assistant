import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';
import { Radar, ShieldAlert, Siren, Timer, UserRound } from 'lucide-react';
import { Badge, SeverityBadge } from '../../components/ui/badge';
import { SEVERITY_META } from '../../lib/severity';
import { Card, CardBody, CardHeader } from '../../components/ui/card';
import { Select } from '../../components/ui/form';
import { LiveDot } from '../../components/ui/live-dot';
import { Segmented } from '../../components/ui/segmented';
import { EmptyState, ErrorState, SkeletonList } from '../../components/ui/states';
import { MACHINES } from '../../lib/constants';
import { useLiveStatus } from '../../lib/live';
import { useAlerts } from '../../lib/queries';
import { cn, formatDateTime } from '../../lib/utils';

const TYPE_ICONS = { Seatbelt: ShieldAlert, Proximity: Radar, Idling: Timer, Anomaly: Siren };
const TYPES = ['All', 'Seatbelt', 'Proximity', 'Idling', 'Anomaly'];
const MAX_VISIBLE = 60;

export default function AlertFeed() {
  const [machine, setMachine] = useState('');
  const [type, setType] = useState('All');
  const { data: alerts = [], isLoading, error, refetch } = useAlerts(machine || null);
  const { status } = useLiveStatus();

  const visible = (type === 'All' ? alerts : alerts.filter((a) => a.type === type)).slice(0, MAX_VISIBLE);

  return (
    <Card>
      <CardHeader
        icon={ShieldAlert}
        title="Alert feed"
        description="System-generated safety alerts, newest first."
        action={
          status === 'open' ? (
            <span className="flex items-center gap-2 text-xs font-semibold text-ok">
              <LiveDot /> Live
            </span>
          ) : (
            <span className="text-xs font-semibold text-warn">Refreshing every 5 s</span>
          )
        }
      />
      <CardBody className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Select
            aria-label="Filter by machine"
            value={machine}
            onChange={(e) => setMachine(e.target.value)}
            options={[{ value: '', label: 'All machines' }, ...MACHINES]}
            className="h-8 w-auto text-xs"
          />
          <Segmented label="Filter by alert type" value={type} onChange={setType} options={TYPES} />
        </div>

        {isLoading && <SkeletonList rows={4} />}
        {error && <ErrorState error={error} onRetry={refetch} />}
        {!isLoading && !error && visible.length === 0 && (
          <EmptyState title="No alerts" description="Nothing has tripped the safety rules for this filter." />
        )}

        <ul className="space-y-2" aria-live="polite">
          <AnimatePresence initial={false}>
            {visible.map((a) => {
              const Icon = TYPE_ICONS[a.type] ?? ShieldAlert;
              const bar = (SEVERITY_META[a.severity] ?? SEVERITY_META.Low).bar;
              return (
                <motion.li
                  key={a.id}
                  layout
                  initial={{ opacity: 0, x: -16, backgroundColor: 'rgba(255,199,44,0.12)' }}
                  animate={{ opacity: 1, x: 0, backgroundColor: 'rgba(25,29,36,1)' }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.35, backgroundColor: { duration: 1.6 } }}
                  className="relative flex items-center gap-4 overflow-hidden rounded-xl border border-line py-3 pr-4 pl-5"
                >
                  <span className={cn('absolute inset-y-0 left-0 w-1', bar)} aria-hidden />
                  <Icon className="size-5 shrink-0 text-muted" aria-hidden />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">{a.message}</p>
                    <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted">
                      <span className="font-semibold text-accent">{a.machine_id}</span>
                      {a.operator_id && a.operator_id !== 'SYSTEM' && (
                        <span className="flex items-center gap-1">
                          <UserRound className="size-3" aria-hidden />
                          {a.operator_id}
                        </span>
                      )}
                      <span>{formatDateTime(a.timestamp)}</span>
                    </p>
                  </div>
                  <Badge className="hidden sm:inline-flex">{a.type}</Badge>
                  <SeverityBadge severity={a.severity} />
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ul>
        {alerts.length > MAX_VISIBLE && type === 'All' && (
          <p className="text-center text-xs text-faint">Showing latest {MAX_VISIBLE} of {alerts.length}</p>
        )}
      </CardBody>
    </Card>
  );
}
