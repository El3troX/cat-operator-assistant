import { animate, motion, useMotionValue, useTransform } from 'motion/react';
import { useEffect } from 'react';

// Rolls to each new value instead of jumping, so live score changes are noticeable.
export function AnimatedNumber({ value, className }) {
  const current = useMotionValue(value);
  const rounded = useTransform(current, (v) => Math.round(v));

  useEffect(() => {
    const controls = animate(current, value, { duration: 0.9, ease: 'easeOut' });
    return () => controls.stop();
  }, [current, value]);

  return <motion.span className={className}>{rounded}</motion.span>;
}
