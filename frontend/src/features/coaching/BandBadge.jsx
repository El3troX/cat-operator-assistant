import { Badge } from '../../components/ui/badge';
import { BAND_META } from '../../lib/coaching';

export default function BandBadge({ band }) {
  const meta = BAND_META[band] ?? BAND_META.Watch;
  const Icon = meta.icon;
  return (
    <Badge tone={meta.tone}>
      <Icon className="size-3.5" aria-hidden />
      {band}
    </Badge>
  );
}
