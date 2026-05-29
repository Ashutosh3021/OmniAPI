import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, id, ...props }, ref) => {
    const checkboxId = id ?? props.name;

    return (
      <label
        htmlFor={checkboxId}
        className={cn("flex items-center gap-sm cursor-pointer", className)}
      >
        <input
          ref={ref}
          type="checkbox"
          id={checkboxId}
          className="h-4 w-4 rounded border-outline text-secondary-fixed focus:ring-secondary-fixed/50"
          {...props}
        />
        <span className="text-body-sm text-on-surface">{label}</span>
      </label>
    );
  }
);

Checkbox.displayName = "Checkbox";
