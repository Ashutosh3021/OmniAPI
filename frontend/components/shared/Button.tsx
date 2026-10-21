import { forwardRef } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md";

const variantClass: Record<Variant, string> = {
  primary: "btn-primary bg-accent border border-transparent",
  secondary:
    "btn-secondary bg-transparent text-ink border border-ink/25 hover:border-accent/45",
  danger: "btn-danger bg-transparent",
  ghost:
    "text-muted hover:text-ink border border-transparent hover:bg-ink/5",
};

const sizeClass: Record<Size, string> = {
  sm: "px-3 py-1.5 text-meta gap-1.5",
  md: "px-4 py-2.5 text-ui gap-2",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  fullWidth?: boolean;
}

/**
 * One treatment per role, taken from the motion verb (fan out, hold, gather).
 * Primary and danger roll their label; secondary floods a wash from the left edge.
 * Utility links (ghost) may change colour only.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
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
        "btn inline-flex items-center justify-center rounded font-medium leading-none tracking-[-0.005em] disabled:pointer-events-none disabled:opacity-50",
        variantClass[variant],
        sizeClass[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      <span className="btn__label inline-flex items-center justify-center gap-[inherit]">
        {children}
      </span>
      <span className="btn__ghost inline-flex items-center justify-center gap-[inherit]" aria-hidden>
        {children}
      </span>
    </button>
  )
);
Button.displayName = "Button";

interface ButtonLinkProps
  extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
}

/** The same treatment as Button, rendered as a real link. Never nest a button in an anchor. */
export function ButtonLink({
  href,
  variant = "primary",
  size = "md",
  fullWidth,
  className,
  children,
  ...props
}: ButtonLinkProps) {
  return (
    <Link
      href={href}
      className={cn(
        "btn inline-flex items-center justify-center rounded font-medium leading-none tracking-[-0.005em]",
        variantClass[variant],
        sizeClass[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      <span className="btn__label inline-flex items-center justify-center gap-[inherit]">
        {children}
      </span>
      <span className="btn__ghost inline-flex items-center justify-center gap-[inherit]" aria-hidden>
        {children}
      </span>
    </Link>
  );
}
