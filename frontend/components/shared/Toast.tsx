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
  success: "border-emerald-500/30 bg-emerald-50 text-emerald-900",
  error: "border-error/30 bg-error-container text-on-error-container",
  info: "border-secondary-fixed/30 bg-surface-container-low text-on-surface",
  warning: "border-amber-500/30 bg-amber-50 text-amber-900",
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
        "flex items-center gap-3 min-w-[280px] max-w-sm px-4 py-3 rounded-lg border shadow-lg",
        styles[type]
      )}
      role="alert"
    >
      <Icon className="h-5 w-5 shrink-0" aria-hidden />
      <p className="text-body-sm flex-1">{message}</p>
      <button
        type="button"
        onClick={onDismiss}
        className="p-1 opacity-70 hover:opacity-100"
        aria-label="Dismiss notification"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
