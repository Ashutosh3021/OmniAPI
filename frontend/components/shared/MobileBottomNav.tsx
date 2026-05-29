"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, GitBranch, Home, Key } from "lucide-react";
import { MOBILE_NAV_ITEMS } from "@/lib/constants";
import { cn } from "@/lib/utils";

const iconMap = {
  Home,
  Key,
  GitBranch,
  BookOpen,
};

export function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 h-16 bg-surface border-t border-outline flex justify-around items-center px-margin-mobile pb-[env(safe-area-inset-bottom)]"
      aria-label="Mobile navigation"
    >
      {MOBILE_NAV_ITEMS.map((item) => {
        const Icon = iconMap[item.icon as keyof typeof iconMap];
        const active =
          pathname === item.href || pathname.startsWith(`${item.href}/`);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center justify-center min-w-[64px] py-1 rounded-lg transition-transform",
              active
                ? "text-secondary-fixed font-semibold"
                : "text-on-surface-variant hover:bg-surface-container-low"
            )}
            aria-current={active ? "page" : undefined}
          >
            <Icon className={cn("h-5 w-5", active && "fill-current")} aria-hidden />
            <span className="text-label-sm mt-0.5">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
