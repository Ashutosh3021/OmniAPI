import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, action, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        "mb-xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-md",
        className
      )}
    >
      <div>
        <h1 className="text-headline-lg-mobile md:text-headline-lg font-semibold text-on-surface tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="text-body-sm text-on-surface-variant mt-xs">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
