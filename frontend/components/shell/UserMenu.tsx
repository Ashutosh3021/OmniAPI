"use client";

import {
  Menu as HeadlessMenu,
  MenuButton,
  MenuItem,
  MenuItems,
} from "@headlessui/react";
import { LogOut, Moon, Sun, User } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/context/ThemeContext";

export function UserMenu() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const initials = (user?.name || "U")
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <HeadlessMenu as="div" className="relative">
      <MenuButton className="flex h-9 items-center gap-2 rounded border border-ink/15 px-2 text-ui text-ink transition-colors hover:border-accent/45 hover:text-accent">
        <span
          className="flex h-6 w-6 items-center justify-center rounded bg-ink/8 font-mono text-micro font-semibold text-ink"
          aria-hidden
        >
          {initials}
        </span>
        <span className="sr-only">Account menu</span>
      </MenuButton>

      <MenuItems
        transition
        anchor="bottom end"
        className="z-50 mt-2 w-60 origin-top-right rounded border border-ink/15 bg-surface p-1 shadow-xl transition duration-150 ease-out [--anchor-gap:8px] data-[closed]:scale-95 data-[closed]:opacity-0 focus:outline-none"
      >
        <div className="border-b border-ink/12 px-3 py-2.5">
          <p className="truncate text-ui font-medium text-ink">
            {user?.name || "Signed in"}
          </p>
          <p className="truncate font-mono text-micro text-muted">
            {user?.email}
          </p>
        </div>

        <MenuItem>
          <button
            type="button"
            onClick={toggleTheme}
            className="flex w-full items-center gap-2.5 rounded px-3 py-2 text-left text-ui text-muted transition-colors data-[focus]:bg-ink/5 data-[focus]:text-ink"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" aria-hidden />
            ) : (
              <Moon className="h-4 w-4" aria-hidden />
            )}
            {theme === "dark" ? "Light theme" : "Dark theme"}
          </button>
        </MenuItem>

        <MenuItem>
          <button
            type="button"
            onClick={logout}
            className="flex w-full items-center gap-2.5 rounded px-3 py-2 text-left text-ui text-bad transition-colors data-[focus]:bg-bad/8"
          >
            <LogOut className="h-4 w-4" aria-hidden />
            Sign out
          </button>
        </MenuItem>
      </MenuItems>
    </HeadlessMenu>
  );
}

export function UserBadge() {
  const { user } = useAuth();

  return (
    <div className="flex items-center gap-2.5">
      <span
        className="flex h-7 w-7 items-center justify-center rounded bg-ink/8 font-mono text-micro font-semibold text-ink"
        aria-hidden
      >
        <User className="h-3.5 w-3.5" />
      </span>
      <span className="min-w-0">
        <span className="block truncate text-meta font-medium text-ink">
          {user?.name || "Signed in"}
        </span>
        <span className="block truncate font-mono text-micro text-muted">
          {user?.email}
        </span>
      </span>
    </div>
  );
}
