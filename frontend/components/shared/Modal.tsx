"use client";

import { Dialog, DialogPanel, DialogTitle } from "@headlessui/react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, children, className }: ModalProps) {
  return (
    <Dialog open={open} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel
          className={cn(
            "w-full max-w-lg rounded-xl bg-white dark:bg-surface p-lg shadow-xl",
            className
          )}
        >
          <div className="flex items-center justify-between mb-md">
            <DialogTitle className="text-headline-sm font-semibold text-on-surface">
              {title}
            </DialogTitle>
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded hover:bg-surface-container-low text-on-surface-variant"
              aria-label="Close dialog"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          {children}
        </DialogPanel>
      </div>
    </Dialog>
  );
}
