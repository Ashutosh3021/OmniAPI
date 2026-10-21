import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

/**
 * The concept's empty state: nothing is patched here yet. It never shows a fake number.
 */
export function EmptyState({
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-start gap-3 border border-dashed border-ink/20 px-5 py-10",
        className
      )}
    >
      <p className="label-wire">empty</p>
      <p className="t-subhead text-ink">{title}</p>
      {description && (
        <p className="max-w-prose text-ui text-muted">{description}</p>
      )}
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}
