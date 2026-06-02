import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, leftIcon, id, ...props }, ref) => {
    const inputId = id ?? props.name;

    return (
      <div className="flex flex-col gap-sm w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="text-label-md font-medium text-dark-gray dark:text-outline"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-light-gray">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              "w-full bg-white dark:bg-surface border border-outline-variant dark:border-outline rounded px-md py-sm text-body-md text-on-surface input-glow transition-all placeholder:text-outline",
              leftIcon && "pl-10",
              error && "border-error",
              className
            )}
            aria-invalid={!!error}
            aria-describedby={error ? `${inputId}-error` : undefined}
            // Suppress hydration warnings for attributes injected by password managers
            suppressHydrationWarning
            {...props}
          />
        </div>
        {error && (
          <p id={`${inputId}-error`} className="text-body-sm text-error" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p className="text-body-sm text-on-surface-variant">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
