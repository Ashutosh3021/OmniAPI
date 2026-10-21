import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  /** A mono stamp that carries real information, such as a count. Never decoration. */
  meta?: string;
  action?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  meta,
  action,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "mb-8 flex flex-col gap-4 border-b border-ink/12 pb-6 sm:flex-row sm:items-end sm:justify-between",
        className
      )}
    >
      <div className="min-w-0">
        <h1 className="t-title text-ink">{title}</h1>
        {description && (
          <p className="mt-2 max-w-prose text-ui text-muted">{description}</p>
        )}
      </div>

      {(meta || action) && (
        <div className="flex shrink-0 flex-col items-start gap-3 sm:items-end">
          {meta && <p className="label-wire">{meta}</p>}
          {action}
        </div>
      )}
    </div>
  );
}
