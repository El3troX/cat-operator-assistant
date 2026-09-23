import { FileWarning, OctagonAlert, Radar, ShieldAlert, ShieldCheck, Timer, TriangleAlert } from 'lucide-react';

export const BAND_META = {
  Good: { tone: 'ok', color: 'var(--color-ok)', text: 'text-ok', icon: ShieldCheck },
  Watch: { tone: 'warn', color: 'var(--color-warn)', text: 'text-warn', icon: TriangleAlert },
  'At risk': { tone: 'danger', color: 'var(--color-danger)', text: 'text-danger', icon: OctagonAlert },
};

// max mirrors the caps in backend/services/scoring.py
export const FACTOR_META = {
  seatbelt: { label: 'Seatbelt', max: 40, icon: ShieldAlert },
  idling: { label: 'Idling', max: 25, icon: Timer },
  proximity: { label: 'Proximity', max: 15, icon: Radar },
  incidents: { label: 'Incidents', max: 20, icon: FileWarning },
};
