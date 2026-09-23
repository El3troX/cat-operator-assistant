import { useState } from 'react';
import { FileWarning, Send } from 'lucide-react';
import { toast } from 'sonner';
import { SEVERITY_META } from '../../lib/severity';
import { Button } from '../../components/ui/button';
import { Card, CardBody, CardHeader } from '../../components/ui/card';
import { Field, Select, Textarea } from '../../components/ui/form';
import { Segmented } from '../../components/ui/segmented';
import { MACHINES, OPERATORS, SEVERITIES } from '../../lib/constants';
import { useCreateIncident } from '../../lib/queries';
import { useSession } from '../../lib/session';
import { cn, nowLocalIso } from '../../lib/utils';

const QUICK_PICKS = ['Near miss', 'Minor collision', 'Equipment fault', 'Ground hazard', 'Person in swing radius', 'Injury'];
const MIN_LENGTH = 5;

const SEVERITY_OPTIONS = SEVERITIES.map((s) => ({
  value: s,
  label: s,
  icon: SEVERITY_META[s].icon,
  activeBg: { Low: 'bg-ok', Medium: 'bg-warn', High: 'bg-danger' }[s],
  activeClass: s === 'High' ? 'text-white' : 'text-canvas',
}));

export default function IncidentForm({ size = 'md' }) {
  const session = useSession();
  const createIncident = useCreateIncident();
  const lg = size === 'lg';
  const [machineId, setMachineId] = useState(session.machineId);
  const [operatorId, setOperatorId] = useState(session.operatorId);
  const [severity, setSeverity] = useState('Medium');
  const [description, setDescription] = useState('');
  const [touched, setTouched] = useState(false);

  // Cab Mode always files against the signed-in cab; Command Center can pick.
  const machine = lg ? session.machineId : machineId;
  const operator = lg ? session.operatorId : operatorId;
  const tooShort = description.trim().length < MIN_LENGTH;

  const addQuickPick = (pick) =>
    setDescription((d) => (d.trim() ? `${d.trim()}. ${pick}` : `${pick}: `));

  const submit = (e) => {
    e.preventDefault();
    setTouched(true);
    if (tooShort) return;
    createIncident.mutate(
      { machine_id: machine, operator_id: operator, severity, description: description.trim(), timestamp: nowLocalIso() },
      {
        onSuccess: (incident) => {
          toast.success(`Incident #${incident.id} logged`, { description: `${incident.severity} · ${incident.machine_id}` });
          setDescription('');
          setTouched(false);
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader
        icon={FileWarning}
        title="Report an incident"
        description={lg ? `Filing for ${machine} · ${operator}` : 'Log collisions, near misses and faults as they happen.'}
      />
      <CardBody>
        <form onSubmit={submit} className="space-y-5" noValidate>
          {!lg && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="Machine">
                {(id) => <Select id={id} value={machineId} onChange={(e) => setMachineId(e.target.value)} options={MACHINES} />}
              </Field>
              <Field label="Operator">
                {(id) => <Select id={id} value={operatorId} onChange={(e) => setOperatorId(e.target.value)} options={OPERATORS} />}
              </Field>
            </div>
          )}

          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">Severity</div>
            <Segmented label="Severity" value={severity} onChange={setSeverity} options={SEVERITY_OPTIONS} size={lg ? 'lg' : 'md'} className="w-full" />
          </div>

          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">Quick pick</div>
            <div className="flex flex-wrap gap-2">
              {QUICK_PICKS.map((pick) => (
                <button
                  key={pick}
                  type="button"
                  onClick={() => addQuickPick(pick)}
                  className={cn(
                    'rounded-full border border-line bg-surface-2 font-medium text-ink transition hover:border-accent/50 hover:text-accent active:scale-95 cursor-pointer',
                    lg ? 'px-4 py-2.5 text-base' : 'px-3 py-1 text-xs',
                  )}
                >
                  {pick}
                </button>
              ))}
            </div>
          </div>

          <Field
            label="What happened?"
            error={touched && tooShort ? `Describe the incident (at least ${MIN_LENGTH} characters).` : undefined}
          >
            {(id) => (
              <Textarea
                id={id}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Clipped the barrier by the east trench, nobody hurt."
                aria-invalid={touched && tooShort}
                className={cn(lg && 'text-base', touched && tooShort && 'border-danger')}
              />
            )}
          </Field>

          <Button type="submit" variant="primary" size={lg ? 'xl' : 'lg'} className="w-full" loading={createIncident.isPending}>
            {!createIncident.isPending && <Send className="size-5" aria-hidden />} Log incident
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}
