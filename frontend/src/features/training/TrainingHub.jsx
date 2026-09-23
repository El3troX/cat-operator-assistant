import { AnimatePresence, motion } from 'motion/react';
import { BadgeCheck, Boxes, CircleCheck, Clock, GraduationCap, MonitorPlay, Play, Presentation } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { EmptyState, ErrorState, SkeletonList } from '../../components/ui/states';
import { useTraining, useUpdateTraining } from '../../lib/queries';
import { cn } from '../../lib/utils';

const FORMAT_META = {
  Video: { icon: MonitorPlay, label: 'E-learning video', action: 'Watch' },
  Simulation: { icon: Boxes, label: 'Simulation', action: 'Launch' },
  Instructor: { icon: Presentation, label: 'Instructor session', action: 'Book' },
};

function ProgressRing({ value, size = 88 }) {
  const stroke = 8;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90" aria-hidden>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--color-surface-3)" strokeWidth={stroke} />
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={c}
        initial={{ strokeDashoffset: c }}
        animate={{ strokeDashoffset: c * (1 - value) }}
        transition={{ type: 'spring', stiffness: 80, damping: 18 }}
      />
    </svg>
  );
}

function ModuleCard({ module, onToggle, lg }) {
  const meta = FORMAT_META[module.format] ?? FORMAT_META.Video;
  const Icon = meta.icon;
  const done = module.completed === 1;
  return (
    <motion.article
      layout
      className={cn(
        'flex flex-col justify-between gap-5 rounded-2xl border p-5 transition-colors',
        done ? 'border-ok/30 bg-ok/5' : 'border-line bg-surface hover:border-line-strong',
      )}
    >
      <div className="flex items-start gap-4">
        <div className={cn('grid shrink-0 place-items-center rounded-xl', lg ? 'size-14' : 'size-12', done ? 'bg-ok/15 text-ok' : 'bg-accent/12 text-accent')}>
          <Icon className={lg ? 'size-7' : 'size-6'} aria-hidden />
        </div>
        <div className="min-w-0">
          <h3 className={cn('font-semibold text-ink', lg ? 'text-xl' : 'text-base')}>{module.title}</h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <Badge>{meta.label}</Badge>
            <span className="flex items-center gap-1 text-xs text-muted">
              <Clock className="size-3.5" aria-hidden /> {module.duration_min} min
            </span>
          </div>
        </div>
      </div>
      <AnimatePresence mode="wait" initial={false}>
        {done ? (
          <motion.div key="done" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2 text-sm font-semibold text-ok">
              <BadgeCheck className="size-5" aria-hidden /> Completed
            </span>
            <Button variant="ghost" size="sm" onClick={() => onToggle(module, 0)}>
              Mark incomplete
            </Button>
          </motion.div>
        ) : (
          <motion.div key="todo" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="grid grid-cols-2 gap-2">
            <Button variant="secondary" size={lg ? 'lg' : 'md'} onClick={() => toast(`${meta.action}: ${module.title}`, { description: 'Content player arrives in the next build.' })}>
              <Play className="size-4" aria-hidden /> {meta.action}
            </Button>
            <Button variant="primary" size={lg ? 'lg' : 'md'} onClick={() => onToggle(module, 1)}>
              <CircleCheck className="size-4" aria-hidden /> Complete
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}

export default function TrainingHub({ size = 'md' }) {
  const { data: modules = [], isLoading, error, refetch } = useTraining();
  const updateTraining = useUpdateTraining();
  const lg = size === 'lg';

  const completed = modules.filter((m) => m.completed === 1).length;
  const progress = modules.length ? completed / modules.length : 0;
  const minutesLeft = modules.filter((m) => m.completed !== 1).reduce((sum, m) => sum + (m.duration_min ?? 0), 0);

  const toggle = (module, value) =>
    updateTraining.mutate(
      { id: module.id, completed: value },
      { onSuccess: () => value === 1 && toast.success('Module completed', { description: module.title }) },
    );

  if (isLoading) return <SkeletonList rows={3} />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;
  if (modules.length === 0) return <EmptyState icon={GraduationCap} title="No training modules yet" />;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-5 rounded-2xl border border-line bg-surface p-5">
        <div className="relative grid place-items-center">
          <ProgressRing value={progress} />
          <span className="absolute text-lg font-bold tabular-nums text-ink">{Math.round(progress * 100)}%</span>
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-muted">Certification progress</div>
          <div className="mt-1 text-2xl font-bold text-ink">
            {completed} of {modules.length} modules
          </div>
          <div className="text-sm text-muted">{minutesLeft ? `${minutesLeft} min of training left` : 'All caught up. Nice work.'}</div>
        </div>
      </div>

      <motion.div layout className={cn('grid gap-4', lg ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3')}>
        {modules.map((m) => (
          <ModuleCard key={m.id} module={m} onToggle={toggle} lg={lg} />
        ))}
      </motion.div>
    </div>
  );
}
