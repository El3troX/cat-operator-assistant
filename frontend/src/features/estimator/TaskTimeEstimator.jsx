import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';
import { BadgeCheck, Calculator, Timer, TriangleAlert } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardBody, CardHeader } from '../../components/ui/card';
import { Field, Select } from '../../components/ui/form';
import { OPERATOR_SKILLS, TASK_TYPES, WEATHERS } from '../../lib/constants';
import { usePredictTaskTime } from '../../lib/queries';

const MACHINE_AGES = Array.from({ length: 10 }, (_, i) => ({ value: String(i + 1), label: `${i + 1} yr${i ? 's' : ''}` }));

const SOURCE_META = {
  model: { tone: 'ok', icon: BadgeCheck, label: 'ML model' },
  historical: { tone: 'warn', icon: TriangleAlert, label: 'Model offline: historical average' },
  heuristic: { tone: 'warn', icon: TriangleAlert, label: 'Model offline: rule-of-thumb estimate' },
};

function SourceBadge({ source }) {
  const meta = SOURCE_META[source] ?? SOURCE_META.heuristic;
  const Icon = meta.icon;
  return (
    <Badge tone={meta.tone} className="mt-3">
      <Icon className="size-3.5" aria-hidden />
      {meta.label}
    </Badge>
  );
}

export default function TaskTimeEstimator() {
  const predict = usePredictTaskTime();
  const [form, setForm] = useState({ task_type: 'Trenching', weather: 'Rainy', operator_skill: 'Intermediate', machine_age_yrs: '4' });
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = (e) => {
    e.preventDefault();
    predict.mutate({ ...form, machine_age_yrs: Number(form.machine_age_yrs) });
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Card>
        <CardHeader icon={Calculator} title="Job conditions" description="Random-forest model trained on historical task data." />
        <CardBody>
          <form onSubmit={submit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Task type">{(id) => <Select id={id} value={form.task_type} onChange={set('task_type')} options={TASK_TYPES} />}</Field>
              <Field label="Weather">{(id) => <Select id={id} value={form.weather} onChange={set('weather')} options={WEATHERS} />}</Field>
              <Field label="Operator skill">
                {(id) => <Select id={id} value={form.operator_skill} onChange={set('operator_skill')} options={OPERATOR_SKILLS} />}
              </Field>
              <Field label="Machine age">
                {(id) => <Select id={id} value={form.machine_age_yrs} onChange={set('machine_age_yrs')} options={MACHINE_AGES} />}
              </Field>
            </div>
            <Button type="submit" variant="primary" size="lg" className="w-full" loading={predict.isPending}>
              Predict duration
            </Button>
          </form>
        </CardBody>
      </Card>

      <Card className="grid min-h-64 place-items-center overflow-hidden">
        <AnimatePresence mode="wait">
          {predict.data ? (
            <motion.div
              key={predict.submittedAt}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 300, damping: 24 }}
              className="p-8 text-center"
              role="status"
            >
              <div className="text-xs font-semibold uppercase tracking-widest text-muted">Predicted duration</div>
              <div className="my-2 text-7xl font-extrabold tabular-nums text-accent">
                {predict.data.predicted_minutes}
                <span className="text-2xl font-semibold text-muted"> min</span>
              </div>
              <p className="text-sm text-muted">
                {predict.variables.task_type} · {predict.variables.weather} · {predict.variables.operator_skill} operator ·{' '}
                {predict.variables.machine_age_yrs} yr machine
              </p>
              <SourceBadge source={predict.data.source} />
            </motion.div>
          ) : (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center gap-2 p-8 text-center">
              <Timer className="size-10 text-faint" aria-hidden />
              <p className="text-sm text-muted">Set the job conditions and run a prediction.</p>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </div>
  );
}
