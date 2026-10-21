import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
  label?: string;
  /** Fills the viewport instead of sitting at the top of the flow. */
  full?: boolean;
}

export function Spinner({ className, label = "Loading", full }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "flex flex-col items-center justify-center gap-3 text-muted",
        full ? "min-h-[60vh]" : "py-14",
        className
      )}
    >
      <Loader2 className="h-5 w-5 animate-spin text-accent" aria-hidden />
      <span className="label-wire">{label}</span>
    </div>
  );
}
