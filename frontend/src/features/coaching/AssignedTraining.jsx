import { AnimatePresence, motion } from 'motion/react';
import { BadgeCheck, CircleCheck, GraduationCap, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../../components/ui/button';
import { useScores, useUpdateTraining } from '../../lib/queries';
import { useSession } from '../../lib/session';

// Training picked for this operator from their own safety factors.
export default function AssignedTraining() {
  const { operatorId } = useSession();
  const { data } = useScores(operatorId);
  const updateTraining = useUpdateTraining();
  const modules = data?.[0]?.recommended_modules ?? [];

  return (
    <section aria-labelledby="assigned-heading" className="rounded-2xl border border-accent/30 bg-accent/5 p-5">
      <h2 id="assigned-heading" className="flex items-center gap-2 text-lg font-bold text-ink">
        <GraduationCap className="size-5 text-accent" aria-hidden /> Assigned to you
      </h2>
      {modules.length === 0 ? (
        <p className="mt-2 flex items-center gap-2 text-sm text-ok">
          <ShieldCheck className="size-4" aria-hidden /> Nothing assigned. Your safety record doesn&apos;t call for extra training.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          <AnimatePresence initial={false}>
            {modules.map((m) => (
              <motion.li
                key={m.id}
                layout
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-surface px-4 py-3"
              >
                <div className="min-w-0">
                  <div className="text-base font-semibold text-ink">{m.title}</div>
                  <div className="text-sm text-muted">
                    Why: {m.reason.charAt(0).toLowerCase() + m.reason.slice(1)} · {m.duration_min} min
                  </div>
                </div>
                {m.completed === 1 ? (
                  <span className="flex items-center gap-1.5 text-sm font-semibold text-ok">
                    <BadgeCheck className="size-5" aria-hidden /> Completed
                  </span>
                ) : (
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={() =>
                      updateTraining.mutate(
                        { id: m.id, completed: 1 },
                        { onSuccess: () => toast.success('Module completed', { description: m.title }) },
                      )
                    }
                  >
                    <CircleCheck className="size-5" aria-hidden /> Mark complete
                  </Button>
                )}
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      )}
    </section>
  );
}
