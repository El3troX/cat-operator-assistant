import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';
import { ClipboardList, UserRound } from 'lucide-react';
import { SeverityBadge } from '../../components/ui/badge';
import { SEVERITY_META } from '../../lib/severity';
import { Card, CardBody, CardHeader } from '../../components/ui/card';
import { Select } from '../../components/ui/form';
import { LiveDot } from '../../components/ui/live-dot';
import { EmptyState, ErrorState, SkeletonList } from '../../components/ui/states';
import { MACHINES } from '../../lib/constants';
import { useLiveStatus } from '../../lib/live';
import { useIncidents } from '../../lib/queries';
import { cn, formatDateTime } from '../../lib/utils';

export default function IncidentList() {
  const [machine, setMachine] = useState('');
  const { data: incidents = [], isLoading, error, refetch } = useIncidents(machine || null);
  const { status } = useLiveStatus();

  return (
    <Card>
      <CardHeader
        icon={ClipboardList}
        title="Incident log"
        description={`${incidents.length} incident${incidents.length === 1 ? '' : 's'} on record`}
        action={
          <div className="flex items-center gap-3">
            {status === 'open' && (
              <span className="hidden items-center gap-2 text-xs font-semibold text-ok sm:flex">
                <LiveDot /> Live
              </span>
            )}
            <Select
              aria-label="Filter by machine"
              value={machine}
              onChange={(e) => setMachine(e.target.value)}
              options={[{ value: '', label: 'All machines' }, ...MACHINES]}
              className="h-8 w-auto text-xs"
            />
          </div>
        }
      />
      <CardBody>
        {isLoading && <SkeletonList rows={3} />}
        {error && <ErrorState error={error} onRetry={refetch} />}
        {!isLoading && !error && incidents.length === 0 && (
          <EmptyState title="No incidents logged" description="Reports filed from the cab or here will appear instantly." />
        )}
        <ul className="space-y-2" aria-live="polite">
          <AnimatePresence initial={false}>
            {incidents.map((inc) => (
              <motion.li
                key={inc.id}
                layout
                initial={{ opacity: 0, y: -10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: 'spring', stiffness: 420, damping: 32 }}
                className="relative overflow-hidden rounded-xl border border-line bg-surface-2 py-3 pr-4 pl-5"
              >
                <span className={cn('absolute inset-y-0 left-0 w-1', (SEVERITY_META[inc.severity] ?? SEVERITY_META.Low).bar)} aria-hidden />
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-ink">{inc.description}</p>
                  <SeverityBadge severity={inc.severity} />
                </div>
                <p className="mt-1 flex flex-wrap items-center gap-x-3 text-xs text-muted">
                  <span className="font-semibold text-accent">{inc.machine_id}</span>
                  <span className="flex items-center gap-1">
                    <UserRound className="size-3" aria-hidden /> {inc.operator_id}
                  </span>
                  <span>{formatDateTime(inc.timestamp)}</span>
                  <span className="text-faint">#{inc.id}</span>
                </p>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      </CardBody>
    </Card>
  );
}
