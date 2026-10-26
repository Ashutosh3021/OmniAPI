interface RingProps {
  /** The part that was served from the cache. */
  value: number;
  /** Everything that was requested. */
  total: number;
  /** The reading in the middle of the ring. */
  caption?: string;
  className?: string;
}

/**
 * A ring, drawn by hand. The charting library cost 90 kB gzipped for one
 * circle, so the circle is a circle.
 */
export function CacheRing({ value, total, caption, className }: RingProps) {
  const ratio = total > 0 ? Math.min(Math.max(value / total, 0), 1) : 0;
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const percent = Math.round(ratio * 100);

  return (
    <div className={`relative grid place-items-center ${className ?? ""}`}>
      <svg viewBox="0 0 140 140" className="h-[180px] w-[180px]" aria-hidden>
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="var(--c-line-strong)"
          strokeWidth="9"
        />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="var(--c-accent)"
          strokeWidth="9"
          strokeDasharray={`${circumference * ratio} ${circumference}`}
          transform="rotate(-90 70 70)"
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <div className="text-center">
          <p className="text-[2rem] font-bold leading-none tracking-[-0.03em] num text-ink [font-variation-settings:'wdth'_108]">
            {percent}%
          </p>
          {caption && (
            <p className="label-wire mt-1.5">{caption}</p>
          )}
        </div>
      </div>
      <span className="sr-only">{percent} percent of calls came from the cache</span>
    </div>
  );
}
