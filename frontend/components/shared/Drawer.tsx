"use client";

import { Dialog, DialogBackdrop, DialogPanel } from "@headlessui/react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  side?: "left" | "right";
  className?: string;
}

export function Drawer({
  open,
  onClose,
  children,
  title,
  side = "left",
  className,
}: DrawerProps) {
  return (
    <Dialog open={open} onClose={onClose} className="relative z-[70] lg:hidden">
      <DialogBackdrop
        transition
        className="fixed inset-0 bg-ink/45 backdrop-blur-[2px] duration-200 data-[closed]:opacity-0"
      />
      <div className="fixed inset-0 flex">
        <DialogPanel
          transition
          className={cn(
            "relative flex h-full w-[288px] max-w-[86vw] flex-col bg-surface",
            side === "left" ? "mr-auto" : "ml-auto",
            className
          )}
        >
          {title && (
            <div className="flex items-center justify-between border-b border-ink/12 px-5 py-4">
              <span className="t-subhead text-ink">{title}</span>
              <button
                type="button"
                onClick={onClose}
                className="rounded p-1.5 text-muted transition-colors hover:bg-ink/5 hover:text-ink"
                aria-label="Close menu"
              >
                <X className="h-5 w-5" aria-hidden />
              </button>
            </div>
          )}
          {children}
        </DialogPanel>
      </div>
    </Dialog>
  );
}
