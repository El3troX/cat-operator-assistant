import { AnimatePresence, motion } from 'motion/react';
import { CircleCheck, Clock, Play, Tractor } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../../components/ui/button';
import { EmptyState, ErrorState, SkeletonList } from '../../components/ui/states';
import { useSession } from '../../lib/session';
import { useTasks, useUpdateTask } from '../../lib/queries';
import { formatTime } from '../../lib/utils';
import StatusBadge from './StatusBadge';

function NextUp({ task, onStart, onComplete, busy }) {
  const started = task.status === 'In Progress';
  return (
    <motion.section
      key={task.id}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="relative overflow-hidden rounded-3xl border border-accent/40 bg-gradient-to-br from-accent/14 via-surface to-surface p-6 sm:p-8"
      aria-labelledby="next-task-title"
    >
      <div className="flex flex-wrap items-center gap-2 text-sm font-semibold uppercase tracking-widest text-accent">
        {started ? 'In progress' : 'Next up'}
        <span className="text-faint">·</span>
        <span className="flex items-center gap-1.5 text-muted normal-case tracking-normal">
          <Tractor className="size-4" aria-hidden /> {task.machine_id}
        </span>
      </div>
      <h2 id="next-task-title" className="mt-3 text-4xl font-extrabold tracking-tight text-ink sm:text-5xl">
        {task.task_type}
      </h2>
      <div className="mt-5 flex flex-wrap gap-x-8 gap-y-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-muted">Scheduled</div>
          <div className="text-2xl font-bold tabular-nums text-ink">{formatTime(task.scheduled_time)}</div>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-muted">Estimated</div>
          <div className="text-2xl font-bold tabular-nums text-ink">
            {task.estimated_time_min ?? '—'}
            <span className="text-base font-medium text-muted"> min</span>
          </div>
        </div>
      </div>
      <div className="mt-7 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Button size="xl" variant={started ? 'secondary' : 'primary'} onClick={onStart} disabled={started || busy}>
          <Play className="size-6" aria-hidden /> {started ? 'Started' : 'Start task'}
        </Button>
        <Button size="xl" variant={started ? 'success' : 'secondary'} onClick={onComplete} disabled={busy}>
          <CircleCheck className="size-6" aria-hidden /> Complete
        </Button>
      </div>
    </motion.section>
  );
}

export default function CabTasks() {
  const { operatorId } = useSession();
  const { data: tasks = [], isLoading, error, refetch } = useTasks();
  const updateTask = useUpdateTask();

  const mine = tasks.filter((t) => t.operator_id === operatorId);
  const open = mine.filter((t) => t.status !== 'Completed');
  const next = open.find((t) => t.status === 'In Progress') ?? open[0];
  const later = open.filter((t) => t !== next);
  const done = mine.filter((t) => t.status === 'Completed');

  const complete = (task) => {
    updateTask.mutate(
      { id: task.id, patch: { status: 'Completed', actual_time_min: task.actual_time_min ?? task.estimated_time_min } },
      { onSuccess: () => toast.success(`${task.task_type} completed`, { description: 'Nice work. Next task is ready.' }) },
    );
  };

  if (isLoading) return <SkeletonList rows={3} />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <AnimatePresence mode="wait">
        {next ? (
          <NextUp
            task={next}
            busy={updateTask.isPending}
            onStart={() => updateTask.mutate({ id: next.id, patch: { status: 'In Progress' } })}
            onComplete={() => complete(next)}
          />
        ) : (
          <EmptyState
            key="empty"
            icon={CircleCheck}
            title={mine.length ? 'All tasks completed' : `No tasks assigned to ${operatorId}`}
            description={mine.length ? 'Great shift. Nothing left on your list.' : 'Switch operator at the top to see another schedule.'}
            className="py-16"
          />
        )}
      </AnimatePresence>

      {later.length > 0 && (
        <section aria-labelledby="later-heading">
          <h3 id="later-heading" className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted">
            Later today · {later.length}
          </h3>
          <ul className="space-y-2">
            {later.map((t) => (
              <li key={t.id} className="flex items-center justify-between gap-4 rounded-2xl border border-line bg-surface px-5 py-4">
                <div className="flex items-center gap-4">
                  <Clock className="size-5 text-faint" aria-hidden />
                  <div>
                    <div className="text-lg font-semibold text-ink">{t.task_type}</div>
                    <div className="text-sm text-muted">
                      {t.machine_id} · {t.estimated_time_min ?? '—'} min
                    </div>
                  </div>
                </div>
                <span className="text-xl font-bold tabular-nums text-ink">{formatTime(t.scheduled_time)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {done.length > 0 && (
        <section aria-labelledby="done-heading">
          <h3 id="done-heading" className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted">
            Done · {done.length}
          </h3>
          <ul className="space-y-2">
            {done.map((t) => (
              <li key={t.id} className="flex items-center justify-between gap-4 rounded-2xl border border-line bg-surface/60 px-5 py-3 opacity-80">
                <span className="font-medium text-ink">{t.task_type}</span>
                <StatusBadge status={t.status} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
