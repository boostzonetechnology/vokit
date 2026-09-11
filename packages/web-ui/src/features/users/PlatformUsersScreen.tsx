import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformUsers } from "./hooks/usePlatformUsers";
import {
  PLATFORM_ROLE_PERMISSIONS,
  PLATFORM_ROLES,
  SENSITIVE_PERMISSIONS,
} from "./types";

type Tab = "users" | "invite" | "rbac" | "sensitive";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "disabled" || value === "revoked") return "danger";
  if (value === "invited" || value === "pending") return "warning";
  return "neutral";
}

export function PlatformUsersScreen() {
  const {
    users,
    invitations,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    inviteUser,
    disableUser,
  } = usePlatformUsers();

  const [tab, setTab] = useState<Tab>("users");
  const [roleView, setRoleView] = useState<string>("super_admin");

  async function onInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await inviteUser({
        email: String(form.get("email") || ""),
        role: String(form.get("role") || "support_admin"),
        principal_type: String(form.get("principal_type") || "platform"),
      });
      event.currentTarget.reset();
      setTab("users");
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "users", label: "Admin users" },
    { id: "invite", label: "Invite" },
    { id: "rbac", label: "Roles / RBAC" },
    { id: "sensitive", label: "Sensitive permissions" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Users / roles
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA18-001–003 · Permissions: users.invite, users.disable
          </p>
        </div>
        <ActionButton variant="secondary" onClick={() => void reload()}>
          Refresh
        </ActionButton>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mb-4 break-all text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              tab === item.id
                ? "rounded-xl bg-brand px-3.5 py-2 text-body font-semibold text-text-inverse"
                : "rounded-xl border border-border-default bg-canvas px-3.5 py-2 text-body font-semibold text-text-secondary"
            }
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === "users" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 grid gap-3 lg:grid-cols-2">
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Email, role…"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Status</span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">All</option>
                <option value="active">active</option>
                <option value="disabled">disabled</option>
              </select>
            </label>
          </div>

          <h2 className="m-0 mb-3 text-section text-text-primary">
            Platform users
            <span className="ml-2 text-body font-normal text-text-muted">({users.length})</span>
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading users…</p>
          ) : users.length === 0 ? (
            <p className="m-0 py-8 text-center text-body text-text-muted">No platform users.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Email</th>
                    <th className="border-0 px-2 py-2 text-left">Role</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Id</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((row) => (
                    <tr
                      key={row.id}
                      className={
                        selectedId === row.id
                          ? "cursor-pointer bg-brand-subtle/40"
                          : "cursor-pointer hover:bg-canvas"
                      }
                      onClick={() => setSelectedId(row.id)}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.email || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.role || "—"}</td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.id.slice(0, 8)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {selected ? (
            <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-border-default bg-canvas p-4">
              <div className="min-w-0 flex-1">
                <p className="m-0 font-semibold text-text-primary">{selected.email}</p>
                <p className="mt-1 mb-0 text-body-sm text-text-muted">
                  {selected.role} · {selected.id}
                </p>
              </div>
              <ActionButton
                variant="outline"
                disabled={busy || selected.status === "disabled"}
                onClick={() => void disableUser(selected.id)}
              >
                Disable user
              </ActionButton>
            </div>
          ) : null}

          {invitations.length > 0 ? (
            <div className="mt-6">
              <h3 className="m-0 mb-2 text-body font-semibold text-text-primary">
                Pending invitations ({invitations.length})
              </h3>
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2 text-left">Email</th>
                      <th className="border-0 px-2 py-2 text-left">Role</th>
                      <th className="border-0 px-2 py-2 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invitations.map((row) => (
                      <tr key={row.id}>
                        <td className="px-2 py-3 text-text-primary">{row.email}</td>
                        <td className="px-2 py-3 text-text-secondary">{row.role}</td>
                        <td className="px-2 py-3">
                          <StatusBadge tone={statusTone(row.status)}>
                            {row.status || "pending"}
                          </StatusBadge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </article>
      ) : null}

      {tab === "invite" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Invite platform user</h2>
          <form className="grid max-w-lg gap-3" onSubmit={(event) => void onInvite(event)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Email</span>
              <input
                name="email"
                type="email"
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Principal type</span>
              <select
                name="principal_type"
                defaultValue="platform"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="platform">platform</option>
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Role</span>
              <select
                name="role"
                defaultValue="support_admin"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                {PLATFORM_ROLES.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </label>
            <ActionButton type="submit" disabled={busy}>
              Send invitation
            </ActionButton>
          </form>
          <div className="mt-4">
            <ApiNote>
              POST /api/v1/platform/users requires users.invite. Invitation token is returned once
              in the create response and delivered by email.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "rbac" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Role permission bundles</h2>
          <div className="mb-4 flex flex-wrap gap-2">
            {PLATFORM_ROLES.map((role) => (
              <button
                key={role}
                type="button"
                className={
                  roleView === role
                    ? "rounded-xl bg-brand px-3 py-1.5 text-body-sm font-semibold text-text-inverse"
                    : "rounded-xl border border-border-default bg-canvas px-3 py-1.5 text-body-sm font-semibold text-text-secondary"
                }
                onClick={() => setRoleView(role)}
              >
                {role}
              </button>
            ))}
          </div>
          <p className="mt-0 mb-3 text-body text-text-secondary">
            {(PLATFORM_ROLE_PERMISSIONS[roleView] ?? []).length} permissions
          </p>
          {(PLATFORM_ROLE_PERMISSIONS[roleView] ?? []).length === 0 ? (
            <p className="m-0 text-body text-text-muted">
              support_admin has an empty permission bundle by design.
            </p>
          ) : (
            <ul className="m-0 grid list-none gap-2 p-0 sm:grid-cols-2">
              {(PLATFORM_ROLE_PERMISSIONS[roleView] ?? []).map((perm) => (
                <li
                  key={perm}
                  className="rounded-xl border border-border-default bg-canvas px-3 py-2 text-body text-text-primary"
                >
                  {perm}
                </li>
              ))}
            </ul>
          )}
          <div className="mt-4">
            <ApiNote>
              SA18-002: roles and permission bundles are defined in the identity catalog. There is
              no API to create custom roles or edit bundles at runtime. Namespaces cannot be mixed.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "sensitive" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Sensitive permission controls
          </h2>
          <p className="mt-0 mb-4 text-body text-text-secondary">
            These permissions stay explicit in the catalog even when unused by a role (SA18-003).
          </p>
          <div className="grid gap-3">
            {SENSITIVE_PERMISSIONS.map((item) => {
              const holders = Object.entries(PLATFORM_ROLE_PERMISSIONS)
                .filter(([, perms]) => perms.includes(item.key))
                .map(([role]) => role);
              return (
                <div
                  key={item.key}
                  className="rounded-xl border border-border-default bg-canvas px-4 py-3"
                >
                  <p className="m-0 font-semibold text-text-primary">{item.label}</p>
                  <p className="mt-1 mb-0 font-mono text-body-sm text-text-muted">{item.key}</p>
                  <p className="mt-2 mb-0 text-body text-text-secondary">
                    Granted to: {holders.length ? holders.join(", ") : "none"}
                  </p>
                </div>
              );
            })}
          </div>
          <div className="mt-4">
            <ApiNote>
              Sensitive permissions are never implied by broad wildcards. Assigning finance_admin
              or compliance_kyc grants only the explicit subset listed above.
            </ApiNote>
          </div>
        </article>
      ) : null}
    </section>
  );
}
