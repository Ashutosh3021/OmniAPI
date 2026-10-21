import { forwardRef, useId } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  hint?: string;
  options: SelectOption[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    { className, label, error, hint, options, placeholder, id, name, ...props },
    ref
  ) => {
    const generated = useId();
    const selectId = id ?? name ?? generated;
    const describedBy = error
      ? `${selectId}-error`
      : hint
        ? `${selectId}-hint`
        : undefined;

    return (
      <div className="flex w-full flex-col gap-1.5">
        {label && (
          <label htmlFor={selectId} className="text-meta font-medium text-ink">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            name={name}
            className={cn("field", error && "border-bad", className)}
            aria-invalid={!!error}
            aria-describedby={describedBy}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <ChevronDown
            className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
            aria-hidden
          />
        </div>
        {error ? (
          <p id={`${selectId}-error`} className="text-meta text-bad" role="alert">
            {error}
          </p>
        ) : hint ? (
          <p id={`${selectId}-hint`} className="text-meta text-muted">
            {hint}
          </p>
        ) : null}
      </div>
    );
  }
);
Select.displayName = "Select";
