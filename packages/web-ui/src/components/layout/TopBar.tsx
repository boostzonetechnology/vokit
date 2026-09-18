import { Search } from "lucide-react";

import type { Portal } from "@/api";
import { PlatformNotificationBell } from "@/features/notifications/components/PlatformNotificationBell";
import { cn } from "@/lib/utils";

export function TopBar({ portal }: { portal: Portal }) {
  return (
    <header
      className="flex h-16 items-center gap-3 border-b border-border-default bg-surface/95 px-5 backdrop-blur supports-[backdrop-filter]:bg-surface/90"
      role="banner"
    >
      <label className="relative m-0 min-w-0 flex-1 font-normal" htmlFor="portal-search">
        <span className="sr-only">Search</span>
        <Search
          className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-text-muted"
          aria-hidden
        />
        <input
          id="portal-search"
          type="search"
          placeholder="Search agencies, customers, agents, or call IDs"
          className={cn(
            "h-10 w-full rounded-xl border border-border-default bg-canvas py-2 pr-3 pl-10 text-body text-text-primary outline-none",
            "placeholder:text-text-muted focus:border-brand focus:bg-surface",
          )}
        />
      </label>

      <div className="flex shrink-0 items-center gap-2.5">
        <span className="hidden items-center gap-2 rounded-xl border border-border-default bg-canvas px-3 py-2 text-body-sm text-text-secondary sm:inline-flex">
          <span className="size-2 rounded-full bg-success" aria-hidden />
          Assistant online
        </span>
        {portal === "platform" ? <PlatformNotificationBell /> : null}
      </div>
    </header>
  );
}
