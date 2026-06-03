"use client";

import { useState, useCallback } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface CopyButtonProps {
  value: string;
  /** Label read by screen readers. Defaults to "Copy to clipboard". */
  label?: string;
  className?: string;
}

/**
 * Single-click clipboard copy with a transient "Copied!" confirmation state.
 * Falls back to the legacy execCommand API when navigator.clipboard is unavailable
 * (e.g. non-HTTPS iframes or older browsers).
 */
export function CopyButton({ value, label = "Copy to clipboard", className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
      } else {
        // Fallback for environments where Clipboard API is unavailable
        const textarea = document.createElement("textarea");
        textarea.value = value;
        textarea.style.cssText = "position:fixed;opacity:0;pointer-events:none;";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Silently fail — the key is still visible for manual selection
    }
  }, [value]);

  return (
    <div className="relative group inline-flex">
      <button
        type="button"
        onClick={handleCopy}
        aria-label={copied ? "Copied!" : label}
        aria-live="polite"
        className={cn(
          "inline-flex items-center justify-center rounded p-1.5 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-800",
          copied
            ? "text-emerald-400 focus:ring-emerald-400"
            : "text-slate-400 hover:text-emerald-400 hover:bg-slate-700 focus:ring-slate-400",
          className
        )}
      >
        {copied ? (
          <Check className="h-4 w-4" aria-hidden />
        ) : (
          <Copy className="h-4 w-4" aria-hidden />
        )}
      </button>

      {/* Tooltip */}
      <span
        role="tooltip"
        className={cn(
          "pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-100 shadow transition-opacity duration-150",
          copied ? "opacity-100" : "opacity-0 group-hover:opacity-100"
        )}
      >
        {copied ? "Copied!" : "Copy"}
      </span>
    </div>
  );
}
