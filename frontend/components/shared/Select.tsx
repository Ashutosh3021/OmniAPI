import { forwardRef } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface SelectOption {
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
  ({ className, label, error, hint, options, placeholder, id, ...props }, ref) => {
    const selectId = id ?? props.name;

    return (
      <div className="flex flex-col gap-sm w-full">
        {label && (
          <label htmlFor={selectId} className="text-label-md font-medium text-on-surface-variant">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={cn(
              "appearance-none w-full bg-white dark:bg-surface border border-outline-variant rounded px-md py-3 text-body-md text-on-surface focus:outline-none focus:border-secondary-fixed focus:ring-2 focus:ring-secondary-fixed/20 cursor-pointer pr-10",
              error && "border-error",
              className
            )}
            aria-invalid={!!error}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-on-surface-variant pointer-events-none" />
        </div>
        {error && <p className="text-body-sm text-error" role="alert">{error}</p>}
        {hint && !error && <p className="text-body-sm text-on-surface-variant">{hint}</p>}
      </div>
    );
  }
);

Select.displayName = "Select";
