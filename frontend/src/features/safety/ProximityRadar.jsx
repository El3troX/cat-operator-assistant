import { AnimatePresence, motion } from 'motion/react';
import { useRef, useState } from 'react';
import { OctagonAlert, Radar, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardBody, CardHeader } from '../../components/ui/card';
import { LiveDot } from '../../components/ui/live-dot';
import { Segmented } from '../../components/ui/segmented';
import { PROXIMITY_ALERT_M } from '../../lib/constants';
import { useMachineTelemetry } from '../../lib/live';
import { markLocalAlerts } from '../../lib/local-alerts';
import { useProximity } from '../../lib/queries';
import { useSession } from '../../lib/session';
import { buzz, cn, nowLocalIso } from '../../lib/utils';

const MAX_M = 12;
const R = 140;
const RINGS = [
  { m: PROXIMITY_ALERT_M, label: '2 m' },
  { m: 5, label: '5 m' },
  { m: 10, label: '10 m' },
];

// sqrt scale keeps the 2 m danger zone large enough to read and touch.
const toRadius = (m) => R * Math.sqrt(Math.min(m, MAX_M) / MAX_M);
const fromRadius = (r) => MAX_M * (Math.min(r, R) / R) ** 2;

const ZONES = [
  { max: PROXIMITY_ALERT_M, label: 'Danger', color: 'var(--color-danger)', text: 'text-danger' },
  { max: 5, label: 'Caution', color: 'var(--color-warn)', text: 'text-warn' },
  { max: 10, label: 'Watch', color: 'var(--color-info)', text: 'text-info' },
  { max: Infinity, label: 'Clear', color: 'var(--color-ok)', text: 'text-ok' },
];
const zoneFor = (m) => ZONES.find((z) => m <= z.max);

const SLIDER_KEYS = new Set(['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'PageUp', 'PageDown']);

const BEARINGS = ['front', 'front-right', 'right', 'rear-right', 'rear', 'rear-left', 'left', 'front-left'];
const bearingLabel = (deg) => BEARINGS[Math.round((((deg % 360) + 360) % 360) / 45) % 8];

const MODES = [
  { value: 'live', label: 'Live' },
  { value: 'test', label: 'Manual test' },
];

function toXY(distance, bearing) {
  const r = toRadius(distance);
  const rad = (bearing * Math.PI) / 180;
  return { x: r * Math.sin(rad), y: -r * Math.cos(rad) };
}

function ExcavatorGlyph() {
  return (
    <g aria-hidden>
      <rect x={-11} y={-4} width={22} height={24} rx={3} fill="var(--color-surface-3)" stroke="var(--color-accent)" strokeWidth={1.5} />
      <rect x={-15} y={-2} width={4} height={20} rx={1.5} fill="var(--color-line-strong)" />
      <rect x={11} y={-2} width={4} height={20} rx={1.5} fill="var(--color-line-strong)" />
      <rect x={-3} y={-26} width={6} height={24} rx={2} fill="var(--color-accent)" />
      <path d="M-7 -30 h14 l-2 6 h-10 z" fill="var(--color-accent)" />
    </g>
  );
}

// Live frames arrive every ~2 s, so glide between them; a dragged blip must track the pointer tightly.
const LIVE_SPRING = { type: 'spring', stiffness: 120, damping: 20 };
const DRAG_SPRING = { type: 'spring', stiffness: 600, damping: 40 };

function Blip({ blip, nearest, live }) {
  const { x, y } = toXY(blip.distance, blip.bearing);
  const color = zoneFor(blip.distance).color;
  return (
    <>
      {nearest && <line x1={0} y1={0} x2={x} y2={y} stroke={color} strokeOpacity={0.35} strokeDasharray="2 4" />}
      <motion.g initial={false} animate={{ x, y }} transition={live ? LIVE_SPRING : DRAG_SPRING}>
        {nearest && (
          <motion.circle r={14} fill={color} fillOpacity={0.18} animate={{ scale: [1, 1.35, 1] }} transition={{ duration: 1.4, repeat: Infinity }} />
        )}
        <circle r={nearest ? 7 : 5} fill={color} fillOpacity={nearest ? 1 : 0.7} stroke="var(--color-canvas)" strokeWidth={2} />
      </motion.g>
    </>
  );
}

export default function ProximityRadar({ size = 'md' }) {
  const { machineId } = useSession();
  const liveReading = useMachineTelemetry(machineId);
  const proximity = useProximity();
  const svgRef = useRef(null);
  const dragging = useRef(false);
  const [mode, setMode] = useState('live');
  const [distance, setDistance] = useState(8);
  const [bearing, setBearing] = useState(-40);
  const [result, setResult] = useState(null);

  const live = mode === 'live' && liveReading;
  const blips = live
    ? liveReading.workers.map((w) => ({ id: w.id, distance: w.distance_m, bearing: w.bearing_deg }))
    : [{ id: 'manual', distance, bearing }];
  const nearest = blips.reduce((a, b) => (b.distance < a.distance ? b : a));
  const zone = zoneFor(nearest.distance);
  const inDanger = nearest.distance <= PROXIMITY_ALERT_M;

  const send = (d = distance) => {
    const timestamp = nowLocalIso();
    markLocalAlerts(['Proximity'], machineId, timestamp);
    proximity.mutate(
      { machine_id: machineId, distance_m: Number(d.toFixed(1)), timestamp },
      {
        onSuccess: (res) => {
          setResult({ ...res, distance: d });
          if (res.triggered) {
            buzz();
            toast.error(`${res.severity} proximity hazard · ${machineId}`, {
              description: `${res.message}. Person ${d.toFixed(1)} m, ${bearingLabel(bearing)}.`,
            });
          }
        },
      },
    );
  };

  const pointerToPolar = (e) => {
    const pt = new DOMPoint(e.clientX, e.clientY).matrixTransform(svgRef.current.getScreenCTM().inverse());
    return { d: Math.max(0.3, fromRadius(Math.hypot(pt.x, pt.y))), b: (Math.atan2(pt.x, -pt.y) * 180) / Math.PI };
  };
  const updateFromPointer = (e) => {
    const { d, b } = pointerToPolar(e);
    setDistance(d);
    setBearing(b);
  };
  const pointerHandlers = live
    ? {}
    : {
        onPointerDown: (e) => {
          dragging.current = true;
          e.currentTarget.setPointerCapture(e.pointerId);
          updateFromPointer(e);
        },
        onPointerMove: (e) => dragging.current && updateFromPointer(e),
        onPointerUp: (e) => {
          if (!dragging.current) return;
          dragging.current = false;
          send(pointerToPolar(e).d);
        },
        onPointerCancel: () => (dragging.current = false),
      };

  return (
    <Card className={cn(inDanger && 'border-danger/60 shadow-[0_0_40px_-12px_var(--color-danger)]', 'transition-[border-color,box-shadow] duration-300')}>
      <CardHeader
        icon={Radar}
        title="Proximity radar"
        description={
          live
            ? `Ground workers around ${machineId}, streamed live. Entering the 2 m zone raises an alert automatically.`
            : 'Drag the worker around the machine. Readings post to the safety engine on release.'
        }
        action={
          liveReading ? (
            <Segmented label="Radar mode" value={mode} onChange={setMode} options={MODES} />
          ) : (
            <span className="text-xs font-semibold text-warn">Live feed offline</span>
          )
        }
      />
      <CardBody className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_220px] lg:items-center">
        <svg
          ref={svgRef}
          viewBox="-160 -160 320 320"
          className={cn('mx-auto w-full touch-none select-none', !live && 'cursor-crosshair', size === 'lg' ? 'max-w-[440px]' : 'max-w-[360px]')}
          role="img"
          aria-label={`Nearest person ${nearest.distance.toFixed(1)} metres ${bearingLabel(nearest.bearing)} of ${machineId}, zone ${zone.label}`}
          {...pointerHandlers}
        >
          <defs>
            <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="var(--color-accent)" stopOpacity="0" />
              <stop offset="1" stopColor="var(--color-accent)" stopOpacity="0.22" />
            </linearGradient>
          </defs>

          <circle r={R + 8} fill="var(--color-canvas)" stroke="var(--color-line)" />
          <circle r={toRadius(PROXIMITY_ALERT_M)} fill="var(--color-danger)" fillOpacity={inDanger ? 0.22 : 0.1} />
          {RINGS.map((ring) => (
            <g key={ring.m}>
              <circle
                r={toRadius(ring.m)}
                fill="none"
                stroke={ring.m === PROXIMITY_ALERT_M ? 'var(--color-danger)' : 'var(--color-line-strong)'}
                strokeDasharray={ring.m === PROXIMITY_ALERT_M ? undefined : '3 5'}
                strokeOpacity={ring.m === PROXIMITY_ALERT_M ? 0.8 : 1}
              />
              <text x={4} y={-toRadius(ring.m) - 4} fontSize={9} fill="var(--color-faint)" fontWeight={600}>
                {ring.label}
              </text>
            </g>
          ))}
          <line x1={-R} y1={0} x2={R} y2={0} stroke="var(--color-line)" />
          <line x1={0} y1={-R} x2={0} y2={R} stroke="var(--color-line)" />

          <motion.g animate={{ rotate: 360 }} transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}>
            {/* full-size circle centers the group's bbox on the machine, so it rotates about the origin */}
            <circle r={R} fill="transparent" />
            <path d={`M0 0 L${R} 0 A${R} ${R} 0 0 0 ${R * Math.cos(-0.6)} ${R * Math.sin(-0.6)} Z`} fill="url(#sweep)" />
          </motion.g>

          <AnimatePresence>
            {inDanger && (
              <motion.circle
                r={toRadius(PROXIMITY_ALERT_M)}
                fill="none"
                stroke="var(--color-danger)"
                strokeWidth={2}
                initial={{ scale: 1, opacity: 0.9 }}
                animate={{ scale: 1.6, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 1.1, repeat: Infinity, ease: 'easeOut' }}
              />
            )}
          </AnimatePresence>

          <ExcavatorGlyph />

          {blips.map((blip) => (
            <Blip key={blip.id} blip={blip} nearest={blip === nearest} live={Boolean(live)} />
          ))}
        </svg>

        <div className="space-y-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-muted">Nearest person</div>
            <div className={cn('text-5xl font-extrabold tabular-nums transition-colors', zone.text)}>
              {nearest.distance.toFixed(1)}
              <span className="text-xl font-semibold text-muted"> m</span>
            </div>
            <div className={cn('mt-1 flex items-center gap-1.5 text-sm font-semibold', zone.text)}>
              {inDanger ? <OctagonAlert className="size-4" aria-hidden /> : <ShieldCheck className="size-4" aria-hidden />}
              {zone.label} zone · {bearingLabel(nearest.bearing)}
            </div>
          </div>

          {live ? (
            <p className="flex items-center gap-2 text-sm text-muted">
              <LiveDot /> Tracking {blips.length} ground workers
            </p>
          ) : (
            <>
              <label className="block">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">Distance</span>
                <input
                  type="range"
                  min={0.3}
                  max={MAX_M}
                  step={0.1}
                  value={distance}
                  onChange={(e) => setDistance(Number(e.target.value))}
                  onPointerUp={(e) => send(Number(e.currentTarget.value))}
                  onKeyUp={(e) => SLIDER_KEYS.has(e.key) && send(Number(e.currentTarget.value))}
                  className="mt-2 w-full accent-[var(--color-accent)]"
                />
              </label>

              <AnimatePresence mode="wait">
                {result && (
                  <motion.div
                    key={`${result.triggered}-${result.distance}`}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    role="status"
                    className={cn(
                      'rounded-xl border px-3 py-2.5 text-sm',
                      result.triggered ? 'border-danger/40 bg-danger/10 text-danger' : 'border-ok/30 bg-ok/8 text-ok',
                    )}
                  >
                    <div className="font-semibold">{result.triggered ? 'Alert logged' : 'Reading OK'}</div>
                    <div className="text-muted">
                      {result.message} ({result.distance.toFixed(1)} m)
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
