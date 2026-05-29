"use client";

import { Dialog, DialogPanel } from "@headlessui/react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  side?: "left" | "right";
  title?: string;
}

export function Drawer({
  open,
  onClose,
  children,
  side = "left",
  title,
}: DrawerProps) {
  return (
    <Dialog open={open} onClose={onClose} className="relative z-50 md:hidden">
      <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
      <div className="fixed inset-0 flex">
        <DialogPanel
          className={cn(
            "relative w-[280px] max-w-[85vw] h-full bg-primary-container flex flex-col shadow-xl",
            side === "left" ? "mr-auto" : "ml-auto"
          )}
        >
          {title && (
            <div className="flex items-center justify-between px-gutter py-lg border-b border-on-primary-container/20">
              <span className="text-headline-md font-extrabold text-white">{title}</span>
              <button
                type="button"
                onClick={onClose}
                className="p-1 text-on-primary-container hover:text-white"
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
          {children}
        </DialogPanel>
      </div>
    </Dialog>
  );
}
