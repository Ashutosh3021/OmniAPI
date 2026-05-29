import { cn } from "@/lib/utils";

const variants = {
  success: "bg-tertiary-fixed-dim/20 text-on-tertiary-fixed-variant",
  error: "bg-error-container text-on-error-container",
  warning: "bg-amber-100 text-amber-800",
  info: "bg-surface-container-high text-secondary",
  neutral: "bg-surface-container-low text-on-surface-variant",
} as const;

interface BadgeProps {
  children: React.ReactNode;
  variant?: keyof typeof variants;
  className?: string;
}

export function Badge({ children, variant = "neutral", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-sm py-xs rounded text-label-sm font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
