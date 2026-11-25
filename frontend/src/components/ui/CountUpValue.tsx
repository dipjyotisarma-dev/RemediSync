"use client";

import * as React from "react";

export interface CountUpValueProps {
  value: number;
  formatter: (val: number) => string;
  durationMs?: number;
}

/**
 * Restrained React Bits CountUp-TS-TW micro-interaction adapted for Operate mode.
 * Hydrates initial KPI numerals smoothly in tabular-nums and respects reduced motion.
 */
export function CountUpValue({
  value,
  formatter,
  durationMs = 360,
}: CountUpValueProps): React.ReactElement {
  const [displayValue, setDisplayValue] = React.useState<number>(value);

  React.useEffect(() => {
    if (
      typeof window === "undefined" ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
      durationMs <= 0
    ) {
      setDisplayValue(value);
      return;
    }

    let rafId = 0;
    const startTime = performance.now();
    const startValue = 0;

    const tick = (now: number): void => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / durationMs);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(startValue + (value - startValue) * eased);
      if (progress < 1) {
        rafId = window.requestAnimationFrame(tick);
      } else {
        setDisplayValue(value);
      }
    };

    rafId = window.requestAnimationFrame(tick);
    return () => {
      window.cancelAnimationFrame(rafId);
    };
  }, [value, durationMs]);

  return <span>{formatter(displayValue)}</span>;
}
