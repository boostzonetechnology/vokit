import { FormEvent, useEffect, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormSectionSkeleton } from "@/components/ui/FormSectionSkeleton";
import { ListRowsSkeleton } from "@/components/ui/ListRowSkeleton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePermissions } from "@/features/auth/hooks/usePermissions";
import { usePlatformPermissions } from "@/features/rbac/hooks/usePlatformPermissions";
import { usePlatformRoles } from "@/features/rbac/hooks/usePlatformRoles";
import { groupPermissionsByModule } from "@/features/rbac/lib/permissionGroups";
import { ApiNote } from "@/features/platform/ux/ApiNote";

function PermissionPicker({
  namespace,
  selected,
  onChange,
  disabled,
}: {
  namespace: string;
  selected: string[];
  onChange: (codes: string[]) => void;
  disabled?: boolean;
}) {
  const { allPermissions, loading, setNamespace } = usePlatformPermissions();

  useEffect(() => {
    setNamespace(namespace);
  }, [namespace, setNamespace]);

  const groups = useMemo(
    () =>
      groupPermissionsByModule(
        allPermissions.filter((row) => !namespace || row.namespace === namespace),
      ),
    [allPermissions, namespace],
  );

  const selectedSet = useMemo(() => new Set(selected), [selected]);

  function toggle(code: string) {
    if (disabled) return;
    if (selectedSet.has(code)) {
      onChange(selected.filter((item) => item !== code));
    } else {
      onChange([...selected, code].sort());
    }
  }

  if (loading && allPermissions.length === 0) {
    return <FormSectionSkeleton fields={4} />;
  }

  return (
    <div className="grid max-h-[420px] gap-4 overflow-auto rounded-xl border border-border-default bg-canvas p-3">
      {groups.length === 0 ? (
        <p className="m-0 text-body text-text-muted">No permissions in this namespace.</p>
      ) : (
        groups.map((group) => (
          <div key={group.module}>
            <p className="m-0 mb-2 text-label font-semibold uppercase text-text-muted">
              {group.module}
            </p>
            <ul className="m-0 grid list-none gap-1.5 p-0 sm:grid-cols-2">
              {group.items.map((item) => (
                <li key={item.id}>
                  <label className="m-0 flex cursor-pointer items-start gap-2 rounded-lg px-2 py-1.5 hover:bg-surface">
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={selectedSet.has(item.code)}
                      disabled={disabled}
                      onChange={() => toggle(item.code)}
                    />
                    <span>
                      <span className="block font-mono text-body-sm text-text-primary">
                        {item.code}
                      </span>
                      {item.is_sensitive ? (
                        <span className="text-body-sm text-danger">Sensitive</span>
                      ) : null}
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </div>
  );
}

export function PlatformRolesScreen() {
  const { can } = usePermissions();
  const canView = can("role.view");
  const canCreate = can("role.create");
  const canUpdate = can("role.update");
  const canDelete = can("role.delete");

  const {
    roles,
    selected,
    selectedId,
    setSelectedId,
    namespace,
    setNamespace,
    error,
    message,
    loading,
    busy,
    reload,
    createRole,
    saveRole,
    removeRole,
  } = usePlatformRoles("");

  const [mode, setMode] = useState<"view" | "create">("view");
  const [displayName, setDisplayName] = useState("");
  const [slug, setSlug] = useState("");
  const [permCodes, setPermCodes] = useState<string[]>([]);

  useEffect(() => {
    if (!selected) {
      setDisplayName("");
      setPermCodes([]);
      return;
    }
    setDisplayName(selected.display_name);
    setPermCodes([...(selected.permissions ?? [])].sort());
    setMode("view");
  }, [selected]);

  const editorNamespace = selected?.namespace ?? "platform";
  const cannotEditSuperAdmin = selected?.slug === "super_admin";
  const cannotDeleteSelected =
    !selected || selected.is_system || selected.slug === "super_admin" || !canDelete;

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    try {
      await createRole({
        slug: slug.trim(),
        display_name: displayName.trim() || slug.trim(),
        permissions: permCodes,
      });
      setSlug("");
      setMode("view");
    } catch {
      /* message in hook */
    }
  }

  async function onSave(event: FormEvent) {
    event.preventDefault();
    if (!selected || cannotEditSuperAdmin) return;
    try {
      await saveRole({
        display_name: displayName.trim(),
        permissions: permCodes,
      });
    } catch {
      /* message in hook */
    }
  }

  if (!canView) {
    return (
      <section className="mx-auto max-w-[720px]">
        <article className="rounded-xl border border-border-default bg-surface p-6">
          <h1 className="m-0 text-[1.5rem] font-bold text-text-primary">Roles</h1>
          <p className="mt-2 mb-0 text-body text-text-muted">
            You do not have permission to view roles (`role.view`).
          </p>
        </article>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Roles
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA18 · Dynamic role bundles · UX only; server enforces authorization
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          {canCreate ? (
            <ActionButton
              variant="outline"
              onClick={() => {
                setMode("create");
                setSelectedId("");
                setSlug("");
                setDisplayName("");
                setPermCodes([]);
              }}
            >
              Create role
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

      <div className="mb-4 flex flex-wrap gap-2">
        {[
          { id: "", label: "All" },
          { id: "platform", label: "Platform" },
          { id: "agency", label: "Agency" },
          { id: "customer", label: "Customer" },
        ].map((item) => (
          <button
            key={item.id || "all"}
            type="button"
            className={
              namespace === item.id
                ? "rounded-xl bg-brand px-3.5 py-2 text-body font-semibold text-text-inverse"
                : "rounded-xl border border-border-default bg-canvas px-3.5 py-2 text-body font-semibold text-text-secondary"
            }
            onClick={() => setNamespace(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Roles
            <span className="ml-2 text-body font-normal text-text-muted">({roles.length})</span>
          </h2>
          {loading && roles.length === 0 ? (
            <ListRowsSkeleton rows={6} />
          ) : roles.length === 0 ? (
            <p className="m-0 text-body text-text-muted">No roles.</p>
          ) : (
            <ul className="m-0 grid list-none gap-2 p-0">
              {roles.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    className={
                      selectedId === row.id
                        ? "w-full rounded-xl border border-brand bg-brand-subtle/40 px-3 py-2.5 text-left"
                        : "w-full rounded-xl border border-border-default bg-canvas px-3 py-2.5 text-left hover:bg-surface"
                    }
                    onClick={() => {
                      setMode("view");
                      setSelectedId(row.id);
                    }}
                  >
                    <span className="block font-semibold text-text-primary">
                      {row.display_name || row.slug}
                    </span>
                    <span className="mt-1 flex flex-wrap items-center gap-2 text-body-sm text-text-muted">
                      <span className="font-mono">{row.slug}</span>
                      <StatusBadge tone={row.is_system ? "warning" : "neutral"}>
                        {row.is_system ? "system" : "custom"}
                      </StatusBadge>
                      <span>{row.namespace}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          {mode === "create" ? (
            <form className="grid gap-4" onSubmit={(event) => void onCreate(event)}>
              <h2 className="m-0 text-section text-text-primary">Create platform role</h2>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Slug</span>
                <input
                  value={slug}
                  onChange={(event) => setSlug(event.target.value)}
                  required
                  pattern="[a-z0-9_\\-]+"
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                  placeholder="platform_ops"
                />
              </label>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Display name</span>
                <input
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                />
              </label>
              <div>
                <p className="mt-0 mb-2 text-body-sm font-semibold text-text-primary">
                  Permissions ({permCodes.length})
                </p>
                <PermissionPicker
                  namespace="platform"
                  selected={permCodes}
                  onChange={setPermCodes}
                />
              </div>
              <ActionButton type="submit" disabled={busy || !canCreate}>
                Create role
              </ActionButton>
              <ApiNote>
                V1: only platform custom roles can be created. PATCH later replaces the full
                permission list.
              </ApiNote>
            </form>
          ) : !selected ? (
            <p className="m-0 text-body text-text-muted">Select a role to view or edit.</p>
          ) : (
            <form className="grid gap-4" onSubmit={(event) => void onSave(event)}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="m-0 text-section text-text-primary">
                    {selected.display_name || selected.slug}
                  </h2>
                  <p className="mt-1 mb-0 font-mono text-body-sm text-text-muted">
                    {selected.slug} · {selected.namespace}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <StatusBadge tone={selected.is_system ? "warning" : "success"}>
                    {selected.is_system ? "system" : "custom"}
                  </StatusBadge>
                  {!cannotDeleteSelected ? (
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => void removeRole(selected.id)}
                    >
                      Delete
                    </ActionButton>
                  ) : null}
                </div>
              </div>

              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Display name</span>
                <input
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  disabled={cannotEditSuperAdmin || !canUpdate}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
                />
              </label>

              <div>
                <p className="mt-0 mb-2 text-body-sm font-semibold text-text-primary">
                  Permissions ({permCodes.length})
                  {cannotEditSuperAdmin ? " · super_admin uses bypass (no pivots)" : ""}
                </p>
                <PermissionPicker
                  namespace={editorNamespace}
                  selected={permCodes}
                  onChange={setPermCodes}
                  disabled={cannotEditSuperAdmin || !canUpdate}
                />
              </div>

              {canUpdate && !cannotEditSuperAdmin ? (
                <ActionButton type="submit" disabled={busy}>
                  Save role
                </ActionButton>
              ) : null}

              <ApiNote>
                Saving sends the full permission set (replace). System roles cannot be deleted.
                Super Admin cannot be modified.
              </ApiNote>
            </form>
          )}
        </article>
      </div>
    </section>
  );
}
