import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const textareaId = id ?? props.name;

    return (
      <div className="flex flex-col gap-sm w-full">
        {label && (
          <label htmlFor={textareaId} className="text-label-md font-medium text-on-surface-variant">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={cn(
            "w-full bg-white dark:bg-surface border border-outline-variant rounded px-md py-sm font-mono text-code text-on-surface input-glow min-h-[120px] resize-y",
            error && "border-error",
            className
          )}
          aria-invalid={!!error}
          {...props}
        />
        {error && <p className="text-body-sm text-error" role="alert">{error}</p>}
      </div>
    );
  }
);

Textarea.displayName = "Textarea";
