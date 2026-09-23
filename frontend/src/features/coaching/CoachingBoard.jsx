import { motion } from 'motion/react';
import { useEffect, useRef } from 'react';
import { BadgeCheck, GraduationCap, OctagonAlert, ShieldCheck, TriangleAlert, UserRound } from 'lucide-react';
import { toast } from 'sonner';
import { PageHeader, StatTile } from '../../components/ui/page-header';
import { EmptyState, ErrorState, SkeletonList } from '../../components/ui/states';
import { FACTOR_META } from '../../lib/coaching';
import { useScores } from '../../lib/queries';
import { cn } from '../../lib/utils';
import BandBadge from './BandBadge';
import ScoreGauge from './ScoreGauge';

function FactorBars({ factors }) {
  return (
    <ul className="space-y-1.5">
      {factors.map((f) => {
        const meta = FACTOR_META[f.factor];
        const Icon = meta.icon;
        return (
          <li key={f.factor} className="grid grid-cols-[88px_1fr_36px] items-center gap-2 text-xs" title={f.detail}>
            <span className="flex items-center gap-1.5 text-muted">
              <Icon className="size-3.5" aria-hidden /> {meta.label}
            </span>
            <span className="h-1.5 overflow-hidden rounded-full bg-surface-3" aria-hidden>
              <motion.span
                className={cn('block h-full rounded-full', f.penalty ? 'bg-danger/80' : 'bg-transparent')}
                initial={false}
                animate={{ width: `${(f.penalty / meta.max) * 100}%` }}
                transition={{ type: 'spring', stiffness: 120, damping: 20 }}
              />
            </span>
            <span className={cn('text-right font-semibold tabular-nums', f.penalty ? 'text-danger' : 'text-faint')}>
              {f.penalty ? `−${f.penalty}` : '0'}
              <span className="sr-only"> points: {f.detail}</span>
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function AssignedList({ modules }) {
  if (!modules.length) {
    return (
      <p className="flex items-center gap-1.5 text-sm text-ok">
        <ShieldCheck className="size-4" aria-hidden /> No training needed
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {modules.map((m) => (
        <li key={m.id} className="rounded-xl border border-line bg-surface-2 px-3 py-2">
          <div className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-1.5 text-sm font-semibold text-ink">
              <GraduationCap className="size-4 text-accent" aria-hidden /> {m.title}
            </span>
            {m.completed === 1 && (
              <span className="flex items-center gap-1 text-xs font-semibold text-ok">
                <BadgeCheck className="size-3.5" aria-hidden /> Done
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-muted">{m.reason}</p>
        </li>
      ))}
    </ul>
  );
}

function OperatorRow({ entry }) {
  return (
    <motion.li
      layout
      className="grid gap-5 rounded-2xl border border-line bg-surface p-5 md:grid-cols-[auto_minmax(0,1fr)_minmax(0,1.1fr)] md:items-center"
    >
      <div className="flex items-center gap-4">
        <ScoreGauge score={entry.score} band={entry.band} size={96} />
        <div>
          <div className="flex items-center gap-1.5 text-lg font-bold text-ink">
            <UserRound className="size-4 text-muted" aria-hidden /> {entry.operator_id}
          </div>
          <BandBadge band={entry.band} />
          <div className="mt-1 text-xs text-faint">{entry.readings} logged readings</div>
        </div>
      </div>
      <FactorBars factors={entry.factors} />
      <AssignedList modules={entry.recommended_modules} />
    </motion.li>
  );
}

// Surfaces live drops so the supervisor sees coaching kick in the moment an incident lands.
function useScoreDropToasts(scores) {
  const previous = useRef(null);
  useEffect(() => {
    if (!scores.length) return;
    const now = Object.fromEntries(scores.map((s) => [s.operator_id, s]));
    if (previous.current) {
      for (const entry of scores) {
        const before = previous.current[entry.operator_id];
        if (!before || entry.score >= before.score) continue;
        const knownIds = new Set(before.recommended_modules.map((m) => m.id));
        const assigned = entry.recommended_modules.filter((m) => !knownIds.has(m.id)).map((m) => m.title);
        toast.warning(`${entry.operator_id} safety score ${before.score} → ${entry.score}`, {
          description: assigned.length ? `Training assigned: ${assigned.join(', ')}` : undefined,
        });
      }
    }
    previous.current = now;
  }, [scores]);
}

export default function CoachingBoard() {
  const { data: scores = [], isLoading, error, refetch } = useScores();
  useScoreDropToasts(scores);

  const count = (band) => scores.filter((s) => s.band === band).length;
  const openAssignments = scores.reduce((n, s) => n + s.recommended_modules.filter((m) => m.completed !== 1).length, 0);

  return (
    <div>
      <PageHeader
        title="Coaching"
        description="Safety score per operator: logged seatbelt and idling behaviour, incidents this shift and proximity breaches in the last hour. Lowest first; training is assigned automatically."
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="At risk" value={count('At risk')} icon={OctagonAlert} tone="text-danger" hint="score below 60" />
        <StatTile label="Watch" value={count('Watch')} icon={TriangleAlert} tone="text-warn" hint="60–79" />
        <StatTile label="Good" value={count('Good')} icon={ShieldCheck} tone="text-ok" hint="80 and above" />
        <StatTile label="Open training" value={openAssignments} icon={GraduationCap} hint="assigned, not yet completed" />
      </div>

      <div className="mt-6">
        {isLoading && <SkeletonList rows={4} />}
        {error && <ErrorState error={error} onRetry={refetch} />}
        {!isLoading && !error && scores.length === 0 && <EmptyState title="No operators yet" description="Scores appear once the operation log is seeded." />}
        <ul className="space-y-3">
          {scores.map((entry) => (
            <OperatorRow key={entry.operator_id} entry={entry} />
          ))}
        </ul>
      </div>
    </div>
  );
}
