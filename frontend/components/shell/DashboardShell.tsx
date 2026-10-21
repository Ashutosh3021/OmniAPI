"use client";

import { useState } from "react";
import { Menu } from "lucide-react";
import { Drawer } from "@/components/shared/Drawer";
import { SpineNav } from "./SpineNav";
import { UserBadge, UserMenu } from "./UserMenu";
import { Wordmark, WordmarkLink } from "./Wordmark";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="min-h-dvh bg-ground">
      {/* The rail: the spine of the whole application. */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-rail flex-col border-r border-ink/12 bg-surface lg:flex">
        <div className="px-6 pb-5 pt-6">
          <WordmarkLink />
        </div>

        <nav className="flex-1 overflow-y-auto px-6" aria-label="Main">
          <SpineNav />
        </nav>

        <div className="border-t border-ink/12 px-6 py-4">
          <UserBadge />
        </div>
      </aside>

      {/* Phone and tablet: one bar, one drawer, one navigation. */}
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-ink/12 bg-surface px-4 lg:hidden">
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          aria-label="Open navigation"
          aria-expanded={drawerOpen}
          className="-ml-2 flex h-10 w-10 items-center justify-center rounded text-ink transition-colors hover:bg-ink/5"
        >
          <Menu className="h-5 w-5" aria-hidden />
        </button>

        <Wordmark className="text-ink" />

        <UserMenu />
      </header>

      <Drawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="OmniAPI"
      >
        <div className="flex-1 overflow-y-auto px-6 py-5">
          <SpineNav onNavigate={() => setDrawerOpen(false)} />
        </div>
        <div className="border-t border-ink/12 px-6 py-4">
          <UserBadge />
        </div>
      </Drawer>

      <main
        id="main"
        tabIndex={-1}
        className="lg:pl-rail"
      >
        <div className="mx-auto w-full max-w-shell px-4 py-8 md:px-8 lg:px-10 lg:py-12">
          {children}
        </div>
      </main>
    </div>
  );
}
