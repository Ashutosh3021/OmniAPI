"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen } from "lucide-react";
import { NAV_ITEMS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { iconMap } from "./icons";

interface SpineNavProps {
  onNavigate?: () => void;
  className?: string;
}

/**
 * The navigation is a spine: one vertical line with a tick for every destination.
 * Hovering extends the tick into a branch and shifts the label along it.
 */
export function SpineNav({ onNavigate, className }: SpineNavProps) {
  const pathname = usePathname();

  return (
    <div className={cn("relative", className)}>
      <span data-pulse-rail className="rail-glow" aria-hidden />
      <svg
        className="pointer-events-none absolute left-0 top-0 h-full w-px"
        preserveAspectRatio="none"
        aria-hidden
      >
        <line
          x1="0.5"
          y1="0"
          x2="0.5"
          y2="100"
          className="fan-spine-base"
          vectorEffect="non-scaling-stroke"
        />
        <line
          data-pulse
          x1="0.5"
          y1="0"
          x2="0.5"
          y2="100"
          className="fan-pulse"
          vectorEffect="non-scaling-stroke"
        />
      </svg>

      <ul className="flex flex-col gap-0.5">
        {NAV_ITEMS.map((item) => {
          const Icon = iconMap[item.icon as keyof typeof iconMap];
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "tick group h-10 text-ui",
                  active
                    ? "font-medium text-ink"
                    : "text-muted hover:text-ink"
                )}
              >
                <span className="tick__label flex items-center gap-3">
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      active ? "text-accent" : "text-muted group-hover:text-ink"
                    )}
                    aria-hidden
                  />
                  <span>{item.label}</span>
                </span>
              </Link>
            </li>
          );
        })}

        <li className="mt-1 border-t border-ink/12 pt-2">
          <Link
            href="/docs"
            onClick={onNavigate}
            aria-current={pathname === "/docs" ? "page" : undefined}
            className={cn(
              "tick group h-10 text-ui",
              pathname === "/docs" ? "font-medium text-ink" : "text-muted hover:text-ink"
            )}
          >
            <span className="tick__label flex items-center gap-3">
              <BookOpen
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors",
                  pathname === "/docs"
                    ? "text-accent"
                    : "text-muted group-hover:text-ink"
                )}
                aria-hidden
              />
              <span>Documentation</span>
            </span>
          </Link>
        </li>
      </ul>
    </div>
  );
}
