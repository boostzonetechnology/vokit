import { CircleHelp, Search } from "lucide-react";

import type { SessionPayload } from "@/api";
import { UserAvatar } from "./UserAvatar";

export function TopBar({
  session,
  onLogout,
}: {
  session: SessionPayload;
  onLogout: () => void;
}) {
  return (
    <header
      className="flex items-center gap-3 border-b border-border-default bg-surface/95 px-5 py-3 backdrop-blur"
      role="banner"
    >
      <label className="relative m-0 min-w-0 flex-1 font-normal" htmlFor="portal-search">
        <span className="sr-only">Search</span>
        <Search
          className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-text-muted"
          aria-hidden
        />
        <input
          id="portal-search"
          type="search"
          placeholder="Search agents, callers, or call IDs."
          className="w-full rounded-lg border border-border-default bg-canvas py-2.5 pr-3 pl-9 text-body text-text-primary outline-none focus:border-brand"
        />
      </label>

      <div className="flex shrink-0 items-center gap-2">
        <span className="inline-flex items-center gap-2 rounded-full border border-border-default bg-canvas px-3 py-1.5 text-body-sm text-text-secondary">
          <span className="size-2 rounded-full bg-success" aria-hidden />
          Assistant online
        </span>
        <button
          type="button"
          className="inline-flex size-9 items-center justify-center rounded-full border border-border-default bg-surface text-text-secondary"
          aria-label="Help"
        >
          <CircleHelp className="size-4" />
        </button>
        <button
          type="button"
          className="rounded-full border-0 bg-transparent p-0"
          onClick={onLogout}
          aria-label={`Sign out ${session.user.email}`}
          title="Sign out"
        >
          <UserAvatar session={session} size="sm" />
        </button>
      </div>
    </header>
  );
}
