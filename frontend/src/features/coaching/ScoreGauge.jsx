import { motion } from 'motion/react';
import { AnimatedNumber } from '../../components/ui/animated-number';
import { BAND_META } from '../../lib/coaching';
import { cn } from '../../lib/utils';

export default function ScoreGauge({ score, band, size = 120, className }) {
  const stroke = Math.round(size * 0.1);
  const radius = (size - stroke) / 2;
  const height = size / 2 + stroke / 2;
  const arcLength = Math.PI * radius;
  const arc = `M ${stroke / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - stroke / 2} ${size / 2}`;
  const color = (BAND_META[band] ?? BAND_META.Watch).color;

  return (
    <div className={cn('relative shrink-0', className)} style={{ width: size, height }} role="img" aria-label={`Safety score ${score} of 100, ${band}`}>
      <svg width={size} height={height} viewBox={`0 0 ${size} ${height}`} aria-hidden>
        <path d={arc} fill="none" stroke="var(--color-surface-3)" strokeWidth={stroke} strokeLinecap="round" />
        <motion.path
          d={arc}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={arcLength}
          initial={{ strokeDashoffset: arcLength }}
          animate={{ strokeDashoffset: arcLength * (1 - score / 100), stroke: color }}
          transition={{ type: 'spring', stiffness: 70, damping: 18 }}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center leading-none" style={{ fontSize: Math.round(size * 0.3) }}>
        <AnimatedNumber value={score} className="font-extrabold tabular-nums text-ink" />
      </div>
    </div>
  );
}
