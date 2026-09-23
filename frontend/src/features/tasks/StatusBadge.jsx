import { CircleCheck, Clock, Play } from 'lucide-react';
import { Badge } from '../../components/ui/badge';

const STATUS_META = {
  Pending: { tone: 'neutral', icon: Clock },
  'In Progress': { tone: 'info', icon: Play },
  Completed: { tone: 'ok', icon: CircleCheck },
};

export default function StatusBadge({ status }) {
  const meta = STATUS_META[status] ?? STATUS_META.Pending;
  const Icon = meta.icon;
  return (
    <Badge tone={meta.tone}>
      <Icon className="size-3.5" aria-hidden />
      {status}
    </Badge>
  );
}
