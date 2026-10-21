import { cn } from "@/lib/utils";

interface MetricStripProps {
  metrics: {
    label: string;
    value: string;
    note?: string;
    tone?: "neutral" | "ok" | "bad";
  }[];
  className?: string;
}

/**
 * Data and facts: the readings sit on one baseline, separated by hairlines
 * rather than boxes. Numbers are set in tabular figures so they do not jitter.
 */
export function MetricStrip({ metrics, className }: MetricStripProps) {
  return (
    <dl
      className={cn(
        "grid grid-cols-1 border-y border-ink/12 sm:grid-cols-3",
        className
      )}
    >
      {metrics.map((m, i) => (
        <div
          key={m.label}
          className={cn(
            "py-5 sm:px-6 sm:py-6",
            i > 0 && "border-t border-ink/12 sm:border-l sm:border-t-0"
          )}
        >
          <dt className="label-wire">{m.label}</dt>
          <dd
            className={cn(
              "mt-2 text-[2rem] font-bold leading-none tracking-[-0.03em] num [font-variation-settings:'wdth'_108]",
              m.tone === "ok" && "text-ok",
              m.tone === "bad" && "text-bad",
              !m.tone && "text-ink"
            )}
          >
            {m.value}
          </dd>
          {m.note && (
            <p className="mt-2 text-meta text-muted">{m.note}</p>
          )}
        </div>
      ))}
    </dl>
  );
}
