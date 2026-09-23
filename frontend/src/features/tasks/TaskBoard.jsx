import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';
import { CircleCheck, Clock, ClipboardList, Play, RefreshCw, Tractor, UserRound } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { PageHeader, StatTile } from '../../components/ui/page-header';
import { Segmented } from '../../components/ui/segmented';
import { EmptyState, ErrorState, SkeletonList } from '../../components/ui/states';
import { TASK_STATUSES } from '../../lib/constants';
import { useTasks, useUpdateTask } from '../../lib/queries';
import { formatTime } from '../../lib/utils';
import StatusBadge from './StatusBadge';

function TaskCard({ task, onStatus }) {
  // The API can't clear actual_time_min, so a task reopened after completion still carries one.
  const showActual = task.status === 'Completed' && task.actual_time_min != null;
  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ type: 'spring', stiffness: 400, damping: 34 }}
      className="flex flex-col justify-between gap-4 rounded-2xl border border-line bg-surface p-5 hover:border-line-strong transition-colors"
    >
      <div>
        <div className="flex items-center justify-between gap-2">
          <Badge tone="accent">
            <Tractor className="size-3.5" aria-hidden />
            {task.machine_id}
          </Badge>
          <StatusBadge status={task.status} />
        </div>
        <h3 className="mt-3 text-lg font-semibold text-ink">{task.task_type}</h3>
        <dl className="mt-3 grid grid-cols-3 gap-2 text-sm">
          <div>
            <dt className="text-xs text-faint">Operator</dt>
            <dd className="mt-0.5 flex items-center gap-1 font-medium text-ink">
              <UserRound className="size-3.5 text-muted" aria-hidden />
              {task.operator_id}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-faint">Scheduled</dt>
            <dd className="mt-0.5 font-medium text-ink tabular-nums">{formatTime(task.scheduled_time)}</dd>
          </div>
          <div>
            <dt className="text-xs text-faint">{showActual ? 'Actual' : 'Estimate'}</dt>
            <dd className="mt-0.5 font-medium tabular-nums text-ink">
              {(showActual ? task.actual_time_min : task.estimated_time_min) ?? '—'}
              <span className="text-muted"> min</span>
            </dd>
          </div>
        </dl>
      </div>
      <Segmented
        label={`Status for task ${task.id}`}
        value={task.status}
        onChange={(status) => onStatus(task, status)}
        options={TASK_STATUSES}
        className="w-full"
      />
    </motion.article>
  );
}

export default function TaskBoard() {
  const { data: tasks = [], isLoading, error, refetch, isFetching } = useTasks();
  const updateTask = useUpdateTask();
  const [filter, setFilter] = useState('All');

  const counts = TASK_STATUSES.reduce((acc, s) => ({ ...acc, [s]: tasks.filter((t) => t.status === s).length }), {});
  const visible = filter === 'All' ? tasks : tasks.filter((t) => t.status === filter);

  const handleStatus = (task, status) => {
    const patch = { status };
    if (status === 'Completed' && task.actual_time_min == null && task.estimated_time_min) {
      patch.actual_time_min = task.estimated_time_min;
    }
    updateTask.mutate({ id: task.id, patch });
  };

  return (
    <div>
      <PageHeader
        title="Daily Tasks"
        description="Today's schedule across the fleet. Status changes save instantly."
        actions={
          <Button size="sm" onClick={() => refetch()} loading={isFetching && !isLoading}>
            {!isFetching && <RefreshCw className="size-3.5" aria-hidden />} Refresh
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Scheduled" value={tasks.length} icon={ClipboardList} />
        <StatTile label="Pending" value={counts.Pending ?? 0} icon={Clock} tone="text-muted" />
        <StatTile label="In progress" value={counts['In Progress'] ?? 0} icon={Play} tone="text-info" />
        <StatTile label="Completed" value={counts.Completed ?? 0} icon={CircleCheck} tone="text-ok" />
      </div>

      <div className="mt-6 mb-4">
        <Segmented label="Filter by status" value={filter} onChange={setFilter} options={['All', ...TASK_STATUSES]} />
      </div>

      {isLoading && <SkeletonList rows={3} />}
      {error && <ErrorState error={error} onRetry={refetch} />}
      {!isLoading && !error && visible.length === 0 && (
        <EmptyState title="No tasks here" description="Nothing matches this filter right now." />
      )}

      <motion.div layout className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <AnimatePresence mode="popLayout">
          {visible.map((task) => (
            <TaskCard key={task.id} task={task} onStatus={handleStatus} />
          ))}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
