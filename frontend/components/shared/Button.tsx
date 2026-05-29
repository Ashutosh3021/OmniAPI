import { forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const variants = {
  primary:
    "bg-secondary-fixed text-white hover:bg-vibrant-cyan-hover focus:ring-secondary-fixed/50",
  secondary:
    "bg-surface border border-outline text-on-surface hover:bg-surface-container-low",
  outline:
    "border border-secondary-fixed text-secondary-fixed hover:bg-secondary-fixed/10",
  danger:
    "bg-error text-white hover:bg-error/90 focus:ring-error/50",
  ghost: "text-on-surface-variant hover:bg-surface-container-low",
} as const;

type Variant = keyof typeof variants;

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      loading,
      fullWidth,
      disabled,
      children,
      ...props
    },
    ref
  ) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded px-md py-sm text-label-md font-medium transition-colors focus:outline-none focus:ring-2 disabled:opacity-60",
        variants[variant],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      {children}
    </button>
  )
);

Button.displayName = "Button";
