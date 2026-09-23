import { Tractor, UserRound } from 'lucide-react';
import { MACHINES, OPERATORS } from '../lib/constants';
import { useSession } from '../lib/session';
import { cn } from '../lib/utils';

function Picker({ icon: Icon, label, value, options, onChange, large }) {
  return (
    <label className={cn('flex items-center gap-2 rounded-lg border border-line bg-surface-2 pl-2.5 focus-within:border-accent', large ? 'h-11' : 'h-8')}>
      <Icon className="size-4 text-accent" aria-hidden />
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn('h-full cursor-pointer bg-transparent pr-2 font-semibold text-ink focus:outline-none', large ? 'text-base' : 'text-xs')}
      >
        {options.map((o) => (
          <option key={o} value={o} className="bg-surface-2">
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function SessionPicker({ large = false }) {
  const { machineId, operatorId, setMachineId, setOperatorId } = useSession();
  return (
    <div className="flex items-center gap-2">
      <Picker icon={Tractor} label="Machine" value={machineId} options={MACHINES} onChange={setMachineId} large={large} />
      <Picker icon={UserRound} label="Operator" value={operatorId} options={OPERATORS} onChange={setOperatorId} large={large} />
    </div>
  );
}
