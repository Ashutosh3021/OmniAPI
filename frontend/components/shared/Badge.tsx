import { cn } from "@/lib/utils";

export type BadgeTone = "ok" | "warn" | "bad" | "accent" | "neutral";

const toneClass: Record<BadgeTone, string> = {
  ok: "text-ok border-ok/30 bg-ok/8",
  warn: "text-warn border-warn/30 bg-warn/8",
  bad: "text-bad border-bad/30 bg-bad/8",
  accent: "text-accent border-accent/30 bg-accent/8",
  neutral: "text-muted border-ink/15 bg-ink/5",
};

const lampClass: Record<BadgeTone, string> = {
  ok: "lamp-ok",
  warn: "lamp-warn",
  bad: "lamp-bad",
  accent: "bg-accent",
  neutral: "lamp-idle",
};

interface BadgeProps {
  children: React.ReactNode;
  tone?: BadgeTone;
  className?: string;
}

/** A status read out on the panel: a lamp and a mono label. */
export function Badge({ children, tone = "neutral", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-2 py-[3px] font-mono text-micro font-medium uppercase tracking-[0.08em]",
        toneClass[tone],
        className
      )}
    >
      <span className={cn("lamp", lampClass[tone])} aria-hidden />
      {children}
    </span>
  );
}
