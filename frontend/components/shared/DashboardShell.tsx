"use client";

import { useState } from "react";
import { Drawer } from "./Drawer";
import { MobileBottomNav } from "./MobileBottomNav";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background text-on-surface antialiased">
      <Navbar onMenuClick={() => setDrawerOpen(true)} />

      <aside className="hidden md:flex flex-col fixed left-0 top-0 h-screen w-[280px] bg-primary-container z-50">
        <Sidebar />
      </aside>

      <Drawer open={drawerOpen} onClose={() => setDrawerOpen(false)} title="OmniAPI">
        <Sidebar onNavigate={() => setDrawerOpen(false)} className="flex-1" />
      </Drawer>

      <main className="md:ml-[280px] pt-16 md:pt-0 pb-20 md:pb-0 min-h-screen">
        <div className="p-margin-mobile md:p-margin-desktop">{children}</div>
      </main>

      <MobileBottomNav />
    </div>
  );
}
