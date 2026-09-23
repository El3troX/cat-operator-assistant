import { Info, OctagonAlert, TriangleAlert } from 'lucide-react';

export const SEVERITY_META = {
  High: { tone: 'danger', icon: OctagonAlert, bar: 'bg-danger' },
  Medium: { tone: 'warn', icon: TriangleAlert, bar: 'bg-warn' },
  Low: { tone: 'ok', icon: Info, bar: 'bg-ok' },
};
