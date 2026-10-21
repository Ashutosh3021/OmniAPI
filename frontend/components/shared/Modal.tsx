"use client";

import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
} from "@headlessui/react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  className,
}: ModalProps) {
  return (
    <Dialog open={open} onClose={onClose} className="relative z-[70]">
      <DialogBackdrop
        transition
        className="fixed inset-0 bg-ink/45 backdrop-blur-[2px] duration-200 data-[closed]:opacity-0"
      />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel
          transition
          className={cn(
            "panel w-full max-w-md p-6 shadow-xl duration-200 data-[closed]:scale-[0.98] data-[closed]:opacity-0",
            className
          )}
        >
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <DialogTitle className="t-subhead text-ink">{title}</DialogTitle>
              {description && (
                <p className="mt-1.5 text-meta text-muted">{description}</p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="-mr-1 -mt-1 rounded p-1.5 text-muted transition-colors hover:bg-ink/5 hover:text-ink"
              aria-label="Close dialog"
            >
              <X className="h-4 w-4" aria-hidden />
            </button>
          </div>

          {children}

          {footer && (
            <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              {footer}
            </div>
          )}
        </DialogPanel>
      </div>
    </Dialog>
  );
}
