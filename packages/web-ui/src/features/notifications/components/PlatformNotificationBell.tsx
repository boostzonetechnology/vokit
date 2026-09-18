import { useEffect, useId, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { Link } from "react-router-dom";

import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePlatformInbox } from "@/features/notifications/hooks/usePlatformInbox";
import { notificationCategoryTone } from "@/features/notifications/lib/eventKind";
import { cn } from "@/lib/utils";

const PREVIEW_LIMIT = 8;

export function PlatformNotificationBell() {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const { inbox, loading, error, unreadCount, reload, markRead } = usePlatformInbox(true);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  async function onOpen() {
    const next = !open;
    setOpen(next);
    if (next) void reload();
  }

  const preview = inbox.slice(0, PREVIEW_LIMIT);

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        onClick={() => void onOpen()}
        className={cn(
          "relative inline-flex size-10 items-center justify-center rounded-xl border border-border-default bg-canvas text-text-secondary transition-colors",
          "hover:border-brand/40 hover:bg-surface hover:text-text-primary",
          open && "border-brand/40 bg-surface text-text-primary",
        )}
        aria-label={unreadCount ? `Notifications, ${unreadCount} unread` : "Notifications"}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
      >
        <Bell className="size-4" strokeWidth={2} aria-hidden />
        {unreadCount > 0 ? (
          <span className="absolute top-1.5 right-1.5 size-2 rounded-full bg-danger" aria-hidden />
        ) : null}
      </button>

      {open ? (
        <div
          id={panelId}
          role="dialog"
          aria-label="Notifications"
          className="absolute top-[calc(100%+0.5rem)] right-0 z-50 w-[min(22.5rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-border-default bg-surface shadow-medium"
        >
          <div className="flex items-center justify-between gap-3 border-b border-border-default px-4 py-3">
            <div>
              <p className="m-0 text-body font-semibold text-text-primary">Notifications</p>
              <p className="m-0 text-body-sm text-text-muted">
                {unreadCount > 0 ? `${unreadCount} unread` : "You're up to date"}
              </p>
            </div>
            <Link
              to="/notifications"
              onClick={() => setOpen(false)}
              className="text-body-sm font-semibold text-text-brand no-underline hover:underline"
            >
              View all
            </Link>
          </div>

          <div className="max-h-[22rem] overflow-y-auto">
            {loading && inbox.length === 0 ? (
              <p className="m-0 px-4 py-6 text-body text-text-muted">Loading…</p>
            ) : null}
            {error ? (
              <p className="m-0 px-4 py-6 text-body text-danger" role="alert">
                {error}
              </p>
            ) : null}
            {!loading && !error && preview.length === 0 ? (
              <p className="m-0 px-4 py-6 text-body text-text-muted">No notifications yet.</p>
            ) : null}

            <ul className="m-0 list-none p-0">
              {preview.map((item) => {
                const unread = !item.read_at;
                return (
                  <li key={item.id} className="border-b border-border-default last:border-b-0">
                    <div
                      className={cn(
                        "flex gap-3 px-4 py-3",
                        unread ? "bg-canvas/80" : "bg-surface",
                      )}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p
                            className={cn(
                              "m-0 truncate text-body text-text-primary",
                              unread ? "font-semibold" : "font-medium",
                            )}
                          >
                            {item.title || "Notification"}
                          </p>
                          {item.category ? (
                            <StatusBadge tone={notificationCategoryTone(item.category)}>
                              {item.category}
                            </StatusBadge>
                          ) : null}
                        </div>
                        {item.body ? (
                          <p className="mt-1 mb-0 line-clamp-2 text-body-sm text-text-secondary">
                            {item.body}
                          </p>
                        ) : null}
                        <p className="mt-1 mb-0 text-body-sm text-text-muted">
                          {item.created_at ? new Date(item.created_at).toLocaleString() : "—"}
                        </p>
                      </div>
                      {unread ? (
                        <button
                          type="button"
                          className="shrink-0 self-start rounded-lg px-2 py-1 text-body-sm font-semibold text-text-brand hover:bg-brand-subtle"
                          onClick={() => void markRead(item.id)}
                        >
                          Mark read
                        </button>
                      ) : null}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="border-t border-border-default px-4 py-3">
            <Link
              to="/notifications"
              onClick={() => setOpen(false)}
              className="inline-flex w-full items-center justify-center rounded-xl border border-border-default bg-canvas px-3 py-2.5 text-body font-semibold text-text-primary no-underline hover:border-brand/40 hover:bg-surface"
            >
              Open notifications page
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
