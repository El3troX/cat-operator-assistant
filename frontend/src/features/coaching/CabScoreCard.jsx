import { ArrowRight } from 'lucide-react';
import { NavLink } from 'react-router';
import { Skeleton } from '../../components/ui/states';
import { useScores } from '../../lib/queries';
import { useSession } from '../../lib/session';
import BandBadge from './BandBadge';
import ScoreGauge from './ScoreGauge';

export default function CabScoreCard() {
  const { operatorId } = useSession();
  const { data, isLoading } = useScores(operatorId);
  const entry = data?.[0];

  if (isLoading) return <Skeleton className="h-28" />;
  if (!entry) return null;

  const topFactor = [...entry.factors].sort((a, b) => b.penalty - a.penalty)[0];
  const open = entry.recommended_modules.filter((m) => m.completed !== 1).length;

  return (
    <section aria-label="Your safety score" className="flex flex-wrap items-center gap-5 rounded-2xl border border-line bg-surface px-5 py-4">
      <ScoreGauge score={entry.score} band={entry.band} size={110} />
      <div className="min-w-0 flex-1">
        <div className="text-xs font-semibold uppercase tracking-wider text-muted">Your safety score</div>
        <div className="mt-1">
          <BandBadge band={entry.band} />
        </div>
        {topFactor?.penalty > 0 && <p className="mt-2 text-sm text-muted">Biggest factor: {topFactor.detail.toLowerCase()}</p>}
      </div>
      {open > 0 && (
        <NavLink
          to="/cab/training"
          className="flex h-12 items-center gap-2 rounded-xl border border-accent/40 bg-accent/10 px-4 text-sm font-semibold text-accent transition hover:bg-accent/20"
        >
          {open} training {open === 1 ? 'module' : 'modules'} assigned <ArrowRight className="size-4" aria-hidden />
        </NavLink>
      )}
    </section>
  );
}
