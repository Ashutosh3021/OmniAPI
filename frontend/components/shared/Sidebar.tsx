"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  GitBranch,
  Key,
  LayoutDashboard,
  Plug,
  Settings,
  Webhook,
} from "lucide-react";
import { NAV_ITEMS } from "@/lib/constants";
import { cn } from "@/lib/utils";

const iconMap = {
  LayoutDashboard,
  Key,
  Plug,
  GitBranch,
  BarChart3,
  Webhook,
  Settings,
};

interface SidebarProps {
  onNavigate?: () => void;
  className?: string;
}

export function Sidebar({ onNavigate, className }: SidebarProps) {
  const pathname = usePathname();

  return (
    <nav className={cn("flex flex-col h-full py-lg", className)} aria-label="Main navigation">
      <div className="px-gutter mb-xl">
        <Link
          href="/dashboard"
          onClick={onNavigate}
          className="text-headline-md font-extrabold text-white tracking-tight"
        >
          OmniAPI
        </Link>
      </div>
      <ul className="flex flex-col gap-xs flex-1 overflow-y-auto px-md">
        {NAV_ITEMS.map((item) => {
          const Icon = iconMap[item.icon as keyof typeof iconMap];
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={onNavigate}
                className={cn(
                  "flex items-center gap-md px-md py-sm rounded transition-all duration-200 border-l-4",
                  active
                    ? "text-secondary-fixed bg-on-primary-fixed-variant border-secondary-fixed"
                    : "text-on-primary-container hover:bg-on-primary-fixed-variant hover:text-white border-transparent"
                )}
                aria-current={active ? "page" : undefined}
              >
                <Icon className="h-5 w-5 shrink-0" aria-hidden />
                <span className="text-label-md">{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="px-md mt-auto pt-lg border-t border-on-primary-container/20">
        <Link
          href="/docs"
          onClick={onNavigate}
          className={cn(
            "flex items-center gap-md px-md py-sm rounded transition-all border-l-4",
            pathname === "/docs"
              ? "text-secondary-fixed bg-on-primary-fixed-variant border-secondary-fixed"
              : "text-on-primary-container hover:bg-on-primary-fixed-variant hover:text-white border-transparent"
          )}
        >
          <BookOpen className="h-5 w-5" aria-hidden />
          <span className="text-label-md">Docs</span>
        </Link>
      </div>
    </nav>
  );
}
