import { CheckCircle, AlertCircle, Info, X, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ToastType } from "@/context/NotificationContext";

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const styles = {
  success: "border-ok/35 bg-ok/10 text-ok",
  error: "border-bad/35 bg-bad/10 text-bad",
  info: "border-accent/35 bg-accent/10 text-accent",
  warning: "border-warn/35 bg-warn/10 text-warn",
};

interface ToastProps {
  message: string;
  type: ToastType;
  onDismiss: () => void;
}

export function Toast({ message, type, onDismiss }: ToastProps) {
  const Icon = icons[type];

  return (
    <div
      className={cn(
        "flex min-w-[260px] max-w-sm items-center gap-3 rounded border px-3.5 py-2.5 shadow-lg backdrop-blur",
        styles[type]
      )}
      role="alert"
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden />
      <p className="flex-1 text-ui">{message}</p>
      <button
        type="button"
        onClick={onDismiss}
        className="rounded p-1 opacity-70 transition-opacity hover:opacity-100"
        aria-label="Dismiss notification"
      >
        <X className="h-4 w-4" aria-hidden />
      </button>
    </div>
  );
}
