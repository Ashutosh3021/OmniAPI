"use client";

import { Menu, User } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Menu as HeadlessMenu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";

interface NavbarProps {
  onMenuClick: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const { user, logout } = useAuth();

  return (
    <header className="md:hidden fixed top-0 left-0 right-0 z-40 h-16 bg-surface border-b border-outline flex items-center justify-between px-margin-mobile">
      <div className="flex items-center gap-md">
        <button
          type="button"
          onClick={onMenuClick}
          className="p-2 text-secondary"
          aria-label="Open navigation menu"
        >
          <Menu className="h-6 w-6" />
        </button>
        <span className="text-headline-md font-bold text-on-surface">OmniAPI</span>
      </div>
      <div className="flex items-center gap-2">
        <HeadlessMenu as="div" className="relative">
          <MenuButton className="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center border border-outline-variant">
            <User className="h-4 w-4 text-on-surface" aria-hidden />
            <span className="sr-only">User menu</span>
          </MenuButton>
          <MenuItems className="absolute right-0 mt-2 w-48 origin-top-right rounded-lg bg-white dark:bg-surface border border-outline shadow-lg py-1 z-50">
            <div className="px-4 py-2 border-b border-outline-variant">
              <p className="text-label-md font-medium truncate">{user?.name}</p>
              <p className="text-label-sm text-on-surface-variant truncate">{user?.email}</p>
            </div>
            <MenuItem>
              <button
                type="button"
                onClick={logout}
                className="w-full text-left px-4 py-2 text-body-sm text-error hover:bg-surface-container-low"
              >
                Sign out
              </button>
            </MenuItem>
          </MenuItems>
        </HeadlessMenu>
      </div>
    </header>
  );
}
