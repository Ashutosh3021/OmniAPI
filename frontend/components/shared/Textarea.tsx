import { forwardRef, useId } from "react";
import { cn } from "@/lib/utils";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  mono?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    { className, label, error, hint, mono = false, id, name, rows = 4, ...props },
    ref
  ) => {
    const generated = useId();
    const fieldId = id ?? name ?? generated;
    const describedBy = error
      ? `${fieldId}-error`
      : hint
        ? `${fieldId}-hint`
        : undefined;

    return (
      <div className="flex w-full flex-col gap-1.5">
        {label && (
          <label htmlFor={fieldId} className="text-meta font-medium text-ink">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={fieldId}
          name={name}
          rows={rows}
          className={cn(
            "field resize-y",
            mono && "font-mono text-[0.8125rem] leading-relaxed",
            className
          )}
          aria-invalid={!!error}
          aria-describedby={describedBy}
          {...props}
        />
        {error ? (
          <p id={`${fieldId}-error`} className="text-meta text-bad" role="alert">
            {error}
          </p>
        ) : hint ? (
          <p id={`${fieldId}-hint`} className="text-meta text-muted">
            {hint}
          </p>
        ) : null}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";
