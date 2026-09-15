import { FormEvent, useEffect, useState } from "react";

import { apiGet, isApiError } from "@/api";
import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { TableSkeleton } from "@/components/ui/TableSkeleton";
import { usePermissions } from "@/features/auth/hooks/usePermissions";
import { asList } from "@/features/platform/lib/list";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePortalRoles } from "@/features/rbac/hooks/usePortalRoles";
import type { RbacNamespace } from "@/features/rbac/types/rbac.types";
import { usePlatformUsers } from "./hooks/usePlatformUsers";

type Tab = "users" | "invite";

type ScopeOption = { id: string; label: string };

const PRINCIPAL_OPTIONS: Array<{ value: RbacNamespace; label: string; help: string }> = [
  {
    value: "platform",
    label: "Platform staff",
    help: "Control-plane user (platform portal only).",
  },
  {
    value: "agency",
    label: "Agency user",
    help: "Belongs to one agency tenant database.",
  },
  {
    value: "customer",
    label: "Customer user",
    help: "Belongs to one customer under an agency.",
  },
];

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "disabled" || value === "revoked") return "danger";
  if (value === "invited" || value === "pending") return "warning";
  return "neutral";
}

function useInviteScopeOptions(principal: RbacNamespace, agencyId: string) {
  const [agencies, setAgencies] = useState<ScopeOption[]>([]);
  const [customers, setCustomers] = useState<ScopeOption[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (principal === "platform") {
      setAgencies([]);
      setCustomers([]);
      setError("");
      return;
    }
    let active = true;
    setLoading(true);
    void apiGet<unknown>("/api/v1/platform/agencies")
      .then((data) => {
        if (!active) return;
        const rows = asList<{ id: string; display_name?: string; name?: string }>(data);
        setAgencies(
          rows.map((row) => ({
            id: row.id,
            label: row.display_name || row.name || row.id.slice(0, 8),
          })),
        );
        setError("");
      })
      .catch((cause) => {
        if (!active) return;
        setAgencies([]);
        setError(isApiError(cause) ? cause.message : "Failed to load agencies.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [principal]);

  useEffect(() => {
    if (principal !== "customer" || !agencyId) {
      setCustomers([]);
      return;
    }
    let active = true;
    setLoading(true);
    const path = `/api/v1/platform/customers?agency_id=${encodeURIComponent(agencyId)}`;
    void apiGet<unknown>(path)
      .then((data) => {
        if (!active) return;
        const rows = asList<{ id: string; display_name?: string; legal_name?: string }>(data);
        setCustomers(
          rows.map((row) => ({
            id: row.id,
            label: row.display_name || row.legal_name || row.id.slice(0, 8),
          })),
        );
      })
      .catch((cause) => {
        if (!active) return;
        setCustomers([]);
        setError(isApiError(cause) ? cause.message : "Failed to load customers.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [principal, agencyId]);

  return { agencies, customers, error, loading };
}

export function PlatformUsersScreen() {
  const { can } = usePermissions();
  const canInvite = can("user.create");
  const canDisable = can("user.delete");
  const canResetMfa = can("mfa.reset");

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
    resetUserMfa,
  } = usePlatformUsers();

  const [tab, setTab] = useState<Tab>("users");
  const [principalType, setPrincipalType] = useState<RbacNamespace>("platform");
  const [agencyId, setAgencyId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [roleSlug, setRoleSlug] = useState("");
  const [mfaResetOpen, setMfaResetOpen] = useState(false);
  const [mfaResetReason, setMfaResetReason] = useState("");

  const {
    roles,
    error: rolesError,
    loading: rolesLoading,
  } = usePortalRoles("platform", principalType);

  const {
    agencies,
    customers,
    error: scopeError,
    loading: scopeLoading,
  } = useInviteScopeOptions(principalType, agencyId);

  useEffect(() => {
    setAgencyId("");
    setCustomerId("");
    setRoleSlug("");
  }, [principalType]);

  useEffect(() => {
    setCustomerId("");
  }, [agencyId]);

  useEffect(() => {
    if (!roles.length) {
      setRoleSlug("");
      return;
    }
    setRoleSlug((current) =>
      roles.some((role) => role.slug === current) ? current : (roles[0]?.slug ?? ""),
    );
  }, [roles]);

  async function onInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!roleSlug) return;
    if (principalType === "agency" && !agencyId) return;
    if (principalType === "customer" && (!agencyId || !customerId)) return;
    try {
      await inviteUser({
        email: String(new FormData(event.currentTarget).get("email") || ""),
        role: roleSlug,
        principal_type: principalType,
        tenant_id: principalType === "platform" ? null : agencyId,
        customer_id: principalType === "customer" ? customerId : null,
      });
      event.currentTarget.reset();
      setPrincipalType("platform");
      setTab("users");
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string; hidden?: boolean }> = [
    { id: "users", label: "Admin users" },
    { id: "invite", label: "Invite", hidden: !canInvite },
  ];

  const principalHelp =
    PRINCIPAL_OPTIONS.find((item) => item.value === principalType)?.help ?? "";

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Users
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA18-001 · Invite by principal namespace + role slug · Permissions: user.create,
            user.delete
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
        {tabs
          .filter((item) => !item.hidden)
          .map((item) => (
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
            Users
            <span className="ml-2 text-body font-normal text-text-muted">({users.length})</span>
          </h2>
          {loading && users.length === 0 ? (
            <TableSkeleton headers={["Email", "Role", "Status", "Id"]} rows={8} />
          ) : users.length === 0 ? (
            <p className="m-0 py-8 text-center text-body text-text-muted">No users.</p>
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
              {canResetMfa ? (
                <ActionButton
                  variant="outline"
                  disabled={busy}
                  onClick={() => {
                    setMfaResetOpen(true);
                    setMfaResetReason("");
                  }}
                >
                  Reset MFA
                </ActionButton>
              ) : null}
              {canDisable ? (
                <ActionButton
                  variant="outline"
                  disabled={busy || selected.status === "disabled"}
                  onClick={() => void disableUser(selected.id)}
                >
                  Disable user
                </ActionButton>
              ) : null}
            </div>
          ) : null}

          {mfaResetOpen && selected && canResetMfa ? (
            <form
              className="mt-3 grid max-w-lg gap-3 rounded-xl border border-border-default bg-canvas p-4"
              onSubmit={(event) => {
                event.preventDefault();
                void resetUserMfa(selected.id, mfaResetReason.trim()).then(() => {
                  setMfaResetOpen(false);
                  setMfaResetReason("");
                });
              }}
            >
              <h3 className="m-0 text-body font-semibold text-text-primary">
                Reset MFA for {selected.email}
              </h3>
              <p className="m-0 text-sm text-text-muted">
                Disables all MFA methods so the user can sign in with password only until they
                re-enroll. A reason is required for audit.
              </p>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Reason</span>
                <input
                  value={mfaResetReason}
                  onChange={(event) => setMfaResetReason(event.target.value)}
                  required
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                />
              </label>
              <div className="flex flex-wrap gap-2">
                <ActionButton type="submit" disabled={busy || !mfaResetReason.trim()}>
                  Confirm reset
                </ActionButton>
                <ActionButton
                  type="button"
                  variant="outline"
                  disabled={busy}
                  onClick={() => {
                    setMfaResetOpen(false);
                    setMfaResetReason("");
                  }}
                >
                  Cancel
                </ActionButton>
              </div>
            </form>
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
                      <th className="border-0 px-2 py-2 text-left">Principal</th>
                      <th className="border-0 px-2 py-2 text-left">Role</th>
                      <th className="border-0 px-2 py-2 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invitations.map((row) => (
                      <tr key={row.id}>
                        <td className="px-2 py-3 text-text-primary">{row.email}</td>
                        <td className="px-2 py-3 text-text-secondary">
                          {row.principal_type || "—"}
                        </td>
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

      {tab === "invite" && canInvite ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Invite user</h2>
          <p className="mt-0 mb-4 text-body text-text-muted">{principalHelp}</p>
          {rolesError ? (
            <p className="mb-3 text-danger" role="alert">
              {rolesError}
            </p>
          ) : null}
          {scopeError ? (
            <p className="mb-3 text-danger" role="alert">
              {scopeError}
            </p>
          ) : null}
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
                value={principalType}
                onChange={(event) => setPrincipalType(event.target.value as RbacNamespace)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                {PRINCIPAL_OPTIONS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            {principalType === "agency" || principalType === "customer" ? (
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Agency</span>
                <select
                  value={agencyId}
                  required
                  disabled={scopeLoading || agencies.length === 0}
                  onChange={(event) => setAgencyId(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  <option value="">Select agency…</option>
                  {agencies.map((agency) => (
                    <option key={agency.id} value={agency.id}>
                      {agency.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            {principalType === "customer" ? (
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Customer</span>
                <select
                  value={customerId}
                  required
                  disabled={!agencyId || scopeLoading || customers.length === 0}
                  onChange={(event) => setCustomerId(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  <option value="">Select customer…</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">
                Role ({principalType} namespace)
              </span>
              <select
                value={roleSlug}
                required
                disabled={rolesLoading || roles.length === 0}
                onChange={(event) => setRoleSlug(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                {rolesLoading ? <option value="">Loading roles…</option> : null}
                {!rolesLoading && roles.length === 0 ? (
                  <option value="">No roles in this namespace</option>
                ) : null}
                {roles.map((role) => (
                  <option key={role.id} value={role.slug}>
                    {role.display_name || role.slug}
                    {role.is_system ? " · system" : " · custom"}
                  </option>
                ))}
              </select>
            </label>

            <ActionButton
              type="submit"
              disabled={
                busy ||
                rolesLoading ||
                !roleSlug ||
                (principalType !== "platform" && !agencyId) ||
                (principalType === "customer" && !customerId)
              }
            >
              Send invitation
            </ActionButton>
          </form>
          <div className="mt-4">
            <ApiNote>
              Principal type chooses the portal membership (platform / agency / customer). Role is
              loaded from GET /platform/roles?namespace=… and must match that namespace. Agency and
              customer invites also send tenant_id / customer_id. MFA reset requires permission
              mfa.reset and records an audited reason.
            </ApiNote>
          </div>
        </article>
      ) : null}
    </section>
  );
}
