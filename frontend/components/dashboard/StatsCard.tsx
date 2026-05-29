import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  label: string;
  value: string;
  subtext?: string;
  subtextVariant?: "positive" | "negative" | "neutral";
  icon: LucideIcon;
}

export function StatsCard({
  label,
  value,
  subtext,
  subtextVariant = "neutral",
  icon: Icon,
}: StatsCardProps) {
  const subtextColors = {
    positive: "text-tertiary-fixed-dim",
    negative: "text-error",
    neutral: "text-on-surface-variant",
  };

  return (
    <div className="bg-white dark:bg-surface border border-outline rounded-xl p-lg flex flex-col">
      <div className="flex items-center justify-between mb-sm">
        <span className="text-label-sm text-on-surface-variant uppercase tracking-wider">
          {label}
        </span>
        <Icon className="h-5 w-5 text-secondary-fixed" aria-hidden />
      </div>
      <div className="text-display text-on-surface">{value}</div>
      {subtext && (
        <p className={cn("text-body-sm mt-sm flex items-center gap-xs", subtextColors[subtextVariant])}>
          {subtext}
        </p>
      )}
    </div>
  );
}
