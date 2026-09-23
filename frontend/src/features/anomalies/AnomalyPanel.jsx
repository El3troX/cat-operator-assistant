import { motion } from 'motion/react';
import { useState } from 'react';
import { Activity, RefreshCw, ShieldAlert, Siren, Timer, UserRound } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardBody, CardHeader } from '../../components/ui/card';
import { Select } from '../../components/ui/form';
import { PageHeader, StatTile } from '../../components/ui/page-header';
import { Segmented } from '../../components/ui/segmented';
import { EmptyState, ErrorState, SkeletonList } from '../../components/ui/states';
import { MACHINES } from '../../lib/constants';
import { useAnomalies } from '../../lib/queries';
import { formatDateTime } from '../../lib/utils';

// backend/routers/anomalies.py caps /anomalies at 100 rows
const ANOMALY_API_LIMIT = 100;

// A reading is typed by its most severe violation; "Anomaly" means the machine flagged it with no rule broken.
const TYPE_META = {
  Idling: { icon: Timer, tone: 'warn', text: 'text-warn' },
  Seatbelt: { icon: ShieldAlert, tone: 'danger', text: 'text-danger' },
  Anomaly: { icon: Siren, tone: 'info', text: 'text-info' },
};
const TYPE_FILTERS = ['All', 'Idling', 'Seatbelt', { value: 'Anomaly', label: 'Other' }];

function countBy(items, key) {
  const counts = new Map();
  for (const item of items) counts.set(item[key], (counts.get(item[key]) ?? 0) + 1);
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

function Hotspots({ title, icon: Icon, rows }) {
  const max = rows[0]?.[1] ?? 1;
  return (
    <Card>
      <CardHeader icon={Icon} title={title} />
      <CardBody>
        {rows.length === 0 ? (
          <p className="text-sm text-muted">No data.</p>
        ) : (
          <ul className="space-y-2.5">
            {rows.slice(0, 5).map(([name, count], i) => (
              <li key={name} className="grid grid-cols-[72px_1fr_32px] items-center gap-3 text-sm">
                <span className="font-semibold text-ink">{name}</span>
                <div className="h-2.5 overflow-hidden rounded-full bg-surface-2">
                  <motion.div
                    className="h-full rounded-full bg-accent"
                    initial={{ width: 0 }}
                    animate={{ width: `${(count / max) * 100}%` }}
                    transition={{ delay: i * 0.05, type: 'spring', stiffness: 120, damping: 20 }}
                  />
                </div>
                <span className="text-right font-semibold tabular-nums text-muted">{count}</span>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

export default function AnomalyPanel() {
  const [machine, setMachine] = useState('');
  const [type, setType] = useState('All');
  const { data: anomalies = [], isLoading, error, refetch, isFetching } = useAnomalies(machine || null);

  const byType = Object.fromEntries(countBy(anomalies, 'type'));
  const visible = type === 'All' ? anomalies : anomalies.filter((a) => a.type === type);

  return (
    <div>
      <PageHeader
        title="Unusual behaviour"
        description="Machine-usage patterns flagged from the operation log: excessive idling, unbelted operation and other machine safety flags."
        actions={
          <>
            <Select
              aria-label="Filter by machine"
              value={machine}
              onChange={(e) => setMachine(e.target.value)}
              options={[{ value: '', label: 'All machines' }, ...MACHINES]}
              className="h-8 w-auto text-xs"
            />
            <Button size="sm" onClick={() => refetch()} loading={isFetching && !isLoading}>
              {!isFetching && <RefreshCw className="size-3.5" aria-hidden />} Refresh
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          label="Flagged"
          value={anomalies.length}
          icon={Activity}
          hint={anomalies.length >= ANOMALY_API_LIMIT ? `most recent ${ANOMALY_API_LIMIT} shown` : 'readings outside limits'}
        />
        <StatTile label="Idling" value={byType.Idling ?? 0} icon={Timer} tone="text-warn" hint="over 45 min per reading" />
        <StatTile label="Unbelted" value={byType.Seatbelt ?? 0} icon={ShieldAlert} tone="text-danger" />
        <StatTile label="Other flags" value={byType.Anomaly ?? 0} icon={Siren} tone="text-info" hint="machine alert, no rule broken" />
      </div>

      {error && <ErrorState error={error} onRetry={refetch} className="mt-6" />}

      <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
        <Card>
          <CardHeader
            icon={Activity}
            title="Flagged readings"
            action={<Segmented label="Filter by type" value={type} onChange={setType} options={TYPE_FILTERS} />}
          />
          <CardBody>
            {isLoading && <SkeletonList rows={5} />}
            {!isLoading && !error && visible.length === 0 && (
              <EmptyState title="No unusual behaviour" description="Every reading is inside normal operating limits." />
            )}
            <ul className="max-h-[560px] space-y-2 overflow-y-auto pr-1">
              {visible.map((a, i) => {
                const meta = TYPE_META[a.type] ?? TYPE_META.Anomaly;
                const Icon = meta.icon;
                return (
                  <li key={`${a.machine_id}-${a.timestamp}-${i}`} className="flex items-center gap-4 rounded-xl border border-line bg-surface-2 px-4 py-3">
                    <Icon className={`size-5 shrink-0 ${meta.text}`} aria-hidden />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-ink">{a.detail}</p>
                      <p className="mt-0.5 flex flex-wrap items-center gap-x-3 text-xs text-muted">
                        <span className="font-semibold text-accent">{a.machine_id}</span>
                        <span className="flex items-center gap-1">
                          <UserRound className="size-3" aria-hidden /> {a.operator_id}
                        </span>
                        <span>{formatDateTime(a.timestamp)}</span>
                      </p>
                    </div>
                    <Badge tone={meta.tone}>
                      <Icon className="size-3.5" aria-hidden />
                      {a.type}
                    </Badge>
                  </li>
                );
              })}
            </ul>
          </CardBody>
        </Card>

        <div className="space-y-4">
          <Hotspots title="Operators to coach" icon={UserRound} rows={countBy(anomalies, 'operator_id')} />
          {!machine && <Hotspots title="Machines to inspect" icon={Activity} rows={countBy(anomalies, 'machine_id')} />}
        </div>
      </div>
    </div>
  );
}
