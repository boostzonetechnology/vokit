import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { ListRowsSkeleton } from "@/components/ui/ListRowSkeleton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { usePermissions } from "@/features/auth/hooks/usePermissions";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyTeam } from "@/features/users/hooks/useAgencyTeam";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active" || value === "accepted") return "success";
  if (value === "invited" || value === "pending") return "warning";
  if (value === "disabled" || value === "revoked") return "danger";
  return "neutral";
}

export function AgencyTeamScreen() {
  const { can } = usePermissions();
  const canInvite = can("team.create");
  const canRevoke = can("team.delete");

  const {
    members,
    roles,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    roleFilter,
    setRoleFilter,
    reload,
    invite,
    revoke,
  } = useAgencyTeam();

  const [showInvite, setShowInvite] = useState(false);
  const defaultRole =
    roles.find((role) => role.slug === "agency_admin")?.slug ?? roles[0]?.slug ?? "";

  async function onInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await invite({
        email: String(form.get("email") || ""),
        role: String(form.get("role") || ""),
      });
      setShowInvite(false);
      event.currentTarget.reset();
    } catch {
      /* hook message */
    }
  }

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Team
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Invite, roles, revoke · AG13 · Roles from GET /agency/roles
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          {canInvite ? (
            <ActionButton variant="outline" onClick={() => setShowInvite((v) => !v)}>
              {showInvite ? "Close" : "Invite user"}
            </ActionButton>
          ) : null}
        </div>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mb-4 text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      {showInvite && canInvite ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => void onInvite(event)}>
            <FormField label="Email" name="email" type="email" required />
            <FormSelect
              label="Role"
              name="role"
              required
              key={defaultRole || "empty"}
              defaultValue={defaultRole}
              disabled={!roles.length}
            >
              {roles.map((role) => (
                <option key={role.id} value={role.slug}>
                  {role.display_name || role.slug}
                </option>
              ))}
            </FormSelect>
            <ActionButton type="submit" disabled={busy || !roles.length}>
              Send invite
            </ActionButton>
          </form>
          <ApiNote>
            AG13-001 / AG13-002 — invite with a role from GET /api/v1/agency/roles (requires
            team.view).
          </ApiNote>
        </article>
      ) : null}

      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        <FormField
          label="Search"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Email, role…"
        />
        <FormSelect
          label="Role filter"
          name="role_filter"
          value={roleFilter}
          onChange={(event) => setRoleFilter(event.target.value)}
        >
          <option value="">All roles</option>
          {roles.map((role) => (
            <option key={role.id} value={role.slug}>
              {role.display_name || role.slug}
            </option>
          ))}
        </FormSelect>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Members ({members.length})
          </h2>
          {loading && members.length === 0 ? (
            <ListRowsSkeleton rows={8} />
          ) : !members.length ? (
            <p className="m-0 text-body text-text-muted">No team members yet.</p>
          ) : (
            <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
              {members.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    className={`w-full rounded-lg border px-3 py-2 text-left ${
                      selectedId === row.id
                        ? "border-border-brand bg-surface-muted"
                        : "border-border-default"
                    }`}
                    onClick={() => setSelectedId(row.id)}
                  >
                    <div className="flex justify-between gap-2">
                      <span className="font-medium text-text-primary">{row.email}</span>
                      <StatusBadge tone={statusTone(row.status)}>{row.status || "—"}</StatusBadge>
                    </div>
                    <p className="m-0 mt-1 text-sm text-text-muted">{row.role}</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">Member detail</h2>
          {!selected ? (
            <p className="m-0 text-body text-text-muted">Select a member.</p>
          ) : (
            <div className="grid gap-3">
              <dl className="m-0 grid gap-2 text-sm">
                <div>
                  <dt className="text-text-muted">Email</dt>
                  <dd className="m-0 text-text-primary">{selected.email}</dd>
                </div>
                <div>
                  <dt className="text-text-muted">Role</dt>
                  <dd className="m-0 text-text-primary">{selected.role}</dd>
                </div>
                <div>
                  <dt className="text-text-muted">Status</dt>
                  <dd className="m-0">
                    <StatusBadge tone={statusTone(selected.status)}>
                      {selected.status || "—"}
                    </StatusBadge>
                  </dd>
                </div>
              </dl>
              {canRevoke && selected.status !== "disabled" ? (
                <ActionButton
                  variant="outline"
                  disabled={busy}
                  onClick={() => {
                    if (
                      window.confirm(
                        `Disable access for ${selected.email}? Active sessions will be revoked.`,
                      )
                    ) {
                      void revoke(selected.id);
                    }
                  }}
                >
                  Revoke access
                </ActionButton>
              ) : null}
              <ApiNote>
                AG13-003 — revoke disables the user and clears sessions. Role changes require a new
                invite today.
              </ApiNote>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
