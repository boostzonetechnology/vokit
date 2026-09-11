import type { ReactNode } from "react";

import type { Portal, SessionPayload } from "@/api";
import { cn } from "@/lib/utils";
import type { NavItem } from "@/nav";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useSidebarCollapsed } from "./useSidebarCollapsed";

export function AppShell({
  portal,
  title,
  nav,
  route,
  session,
  onLogout,
  children,
}: {
  portal: Portal;
  title: string;
  nav: NavItem[];
  route: string;
  session: SessionPayload;
  onLogout: () => void;
  children: ReactNode;
}) {
  const { collapsed, toggle } = useSidebarCollapsed(false);

  return (
    <div className="min-h-screen bg-canvas">
      <a
        className="absolute left-3 top-[-48px] z-50 rounded-md bg-text-primary px-3 py-2 text-text-inverse focus:top-3"
        href="#main"
      >
        Skip to main content
      </a>

      <Sidebar
        portal={portal}
        title={title}
        nav={nav}
        route={route}
        session={session}
        collapsed={collapsed}
        onToggle={toggle}
        onLogout={onLogout}
      />

      {/* Content shifts with sidebar width; only this column scrolls */}
      <div
        className={cn(
          "flex min-h-screen flex-col transition-[padding] duration-200 ease-out",
          collapsed ? "pl-[72px]" : "pl-[260px]",
        )}
      >
        <div className="sticky top-0 z-30">
          <TopBar session={session} onLogout={onLogout} />
        </div>
        <main id="main" className="min-h-0 flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
