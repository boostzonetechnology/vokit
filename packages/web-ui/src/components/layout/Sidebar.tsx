import { LogOut, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { NavLink } from "react-router-dom";

import type { Portal, SessionPayload } from "@/api";
import { cn } from "@/lib/utils";
import type { NavItem } from "@/nav";
import { portalNavGroups } from "./navGroups";
import { UserAvatar } from "./UserAvatar";

/** Shared icon size for sidebar controls + nav glyphs */
const ICON = "size-5";
const ICON_HIT = "inline-flex size-10 shrink-0 items-center justify-center rounded-lg";

export function Sidebar({
  portal,
  title,
  nav,
  route,
  session,
  collapsed,
  onToggle,
  onLogout,
}: {
  portal: Portal;
  title: string;
  nav: NavItem[];
  route: string;
  session: SessionPayload;
  collapsed: boolean;
  onToggle: () => void;
  onLogout: () => void;
}) {
  const groups = portalNavGroups(portal, nav);
  const productTitle = portal === "platform" ? "Vokit Platform" : title;
  const productMeta = portal === "platform" ? "v 1.0" : `${portal} portal`;

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 flex flex-col border-r border-border-default bg-surface transition-[width] duration-200 ease-out",
        collapsed ? "w-[72px]" : "w-[260px]",
      )}
      aria-label="Primary"
    >
      {/* Brand header */}
      <div
        className={cn(
          "flex shrink-0 border-b border-border-default",
          collapsed ? "flex-col items-center gap-1 px-2 py-3" : "h-16 items-center gap-2 px-2",
        )}
      >
        <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand text-base font-bold text-text-inverse">
          V
        </span>
        {!collapsed ? (
          <div className="min-w-0 flex-1">
            <p className="m-0 truncate text-body font-semibold text-text-primary">{productTitle}</p>
            <p className="m-0 truncate text-body-sm text-text-muted">{productMeta}</p>
          </div>
        ) : null}
        <button
          type="button"
          onClick={onToggle}
          className={cn(ICON_HIT, "text-text-secondary hover:bg-canvas hover:text-text-primary")}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <PanelLeftOpen className={ICON} strokeWidth={2} />
          ) : (
            <PanelLeftClose className={ICON} strokeWidth={2} />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav
        className={cn("min-h-0 flex-1 overflow-y-auto py-3", collapsed ? "px-2" : "px-3")}
        aria-label="Portal"
      >
        {groups.map((group) => (
          <div key={group.id} className="mb-3">
            {!collapsed ? (
              <p className="mb-1.5 px-2.5 text-label uppercase tracking-wide text-text-muted">
                {group.label}
              </p>
            ) : (
              <div className="mx-auto mb-2 h-px w-8 bg-border-default" aria-hidden />
            )}
            <ul className="m-0 list-none p-0">
              {group.items.map((item) => {
                const itemRoute = item.href.replace(/^\/+/, "");
                const isActive = itemRoute === route || route.startsWith(`${itemRoute}/`);
                const Icon = item.icon;
                const label = item.label;

                return (
                  <li key={item.href} className="relative mb-0.5">
                    <NavLink
                      to={item.href}
                      title={collapsed ? label : undefined}
                      className={cn(
                        "group relative flex items-center rounded-lg text-body no-underline transition-colors",
                        collapsed ? "h-10 justify-center" : "h-10 gap-3 px-2.5",
                        isActive
                          ? "bg-canvas font-semibold text-text-primary"
                          : "text-text-secondary hover:bg-canvas/80 hover:text-text-primary",
                      )}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <Icon className={cn(ICON, "shrink-0")} strokeWidth={2} aria-hidden />
                      {!collapsed ? <span className="truncate">{label}</span> : null}

                      {collapsed ? (
                        <span
                          className="pointer-events-none absolute top-1/2 left-[calc(100%+10px)] z-50 -translate-y-1/2 rounded-md bg-text-primary px-2.5 py-1.5 text-body-sm whitespace-nowrap text-text-inverse opacity-0 shadow-medium transition-opacity group-hover:opacity-100"
                          role="tooltip"
                        >
                          {label}
                        </span>
                      ) : null}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* User footer + logout */}
      <div
        className={cn(
          "shrink-0 border-t border-border-default",
          collapsed ? "flex flex-col items-center gap-1 p-2" : "px-2 py-3",
        )}
      >
        {collapsed ? (
          <>
            <div className="relative group">
              <UserAvatar session={session} size="sm" />
              <span
                className="pointer-events-none absolute top-1/2 left-[calc(100%+10px)] z-50 -translate-y-1/2 rounded-md bg-text-primary px-2.5 py-1.5 text-body-sm whitespace-nowrap text-text-inverse opacity-0 shadow-medium transition-opacity group-hover:opacity-100"
                role="tooltip"
              >
                {session.user.email}
              </span>
            </div>
            <button
              type="button"
              onClick={onLogout}
              className={cn(ICON_HIT, "text-text-secondary hover:bg-canvas hover:text-danger")}
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut className={ICON} strokeWidth={2} />
            </button>
          </>
        ) : (
          <div className="flex items-center gap-2 rounded-lg px-1 py-1">
            <UserAvatar session={session} size="sm" />
            <div className="min-w-0 flex-1">
              <p className="m-0 truncate text-body font-semibold text-text-primary">
                {session.user.email.split("@")[0]}
              </p>
              <p className="m-0 truncate text-body-sm text-text-muted">{session.user.email}</p>
            </div>
            <button
              type="button"
              onClick={onLogout}
              className={cn(ICON_HIT, "text-text-secondary hover:bg-canvas hover:text-danger")}
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut className={ICON} strokeWidth={2} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
