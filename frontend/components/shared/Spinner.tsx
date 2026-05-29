import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
  label?: string;
}

export function Spinner({ className, label = "Loading" }: SpinnerProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2 py-xl", className)} role="status">
      <Loader2 className="h-8 w-8 animate-spin text-secondary-fixed" aria-hidden />
      <span className="sr-only">{label}</span>
    </div>
  );
}
