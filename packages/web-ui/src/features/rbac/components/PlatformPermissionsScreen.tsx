import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TableSkeleton } from "@/components/ui/TableSkeleton";
import { usePermissions } from "@/features/auth/hooks/usePermissions";
import { usePlatformPermissions } from "@/features/rbac/hooks/usePlatformPermissions";
import { ApiNote } from "@/features/platform/ux/ApiNote";

export function PlatformPermissionsScreen() {
  const { can } = usePermissions();
  const canView = can("permission.view");
  const canCreate = can("permission.create");
  const canSync = can("permission.sync");

  const {
    permissions,
    namespace,
    setNamespace,
    module,
    setModule,
    sensitiveOnly,
    setSensitiveOnly,
    error,
    message,
    loading,
    busy,
    reload,
    createPermission,
    syncCatalog,
  } = usePlatformPermissions();

  const [showCreate, setShowCreate] = useState(false);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createPermission({
        namespace: String(form.get("namespace") || "platform"),
        code: String(form.get("code") || "").trim(),
        description: String(form.get("description") || "").trim(),
        is_sensitive: form.get("is_sensitive") === "on",
      });
      event.currentTarget.reset();
      setShowCreate(false);
    } catch {
      /* hook message */
    }
  }

  if (!canView) {
    return (
      <section className="mx-auto max-w-[720px]">
        <article className="rounded-xl border border-border-default bg-surface p-6">
          <h1 className="m-0 text-[1.5rem] font-bold text-text-primary">Permissions</h1>
          <p className="mt-2 mb-0 text-body text-text-muted">
            You do not have permission to view the permission catalog (`permission.view`).
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
            Permissions
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA18-003 · Catalog codes · sync is additive only
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          {canSync ? (
            <ActionButton variant="outline" disabled={busy} onClick={() => void syncCatalog()}>
              Sync catalog
            </ActionButton>
          ) : null}
          {canCreate ? (
            <ActionButton onClick={() => setShowCreate((value) => !value)}>
              {showCreate ? "Close" : "Create permission"}
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

      {showCreate ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => void onCreate(event)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Namespace</span>
              <select
                name="namespace"
                defaultValue="platform"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="platform">platform</option>
                <option value="agency">agency</option>
                <option value="customer">customer</option>
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Code</span>
              <input
                name="code"
                required
                placeholder="module.action"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 font-mono text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal sm:col-span-2">
              <span className="text-body-sm text-text-muted">Description</span>
              <input
                name="description"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 flex items-center gap-2 font-normal">
              <input type="checkbox" name="is_sensitive" />
              <span className="text-body text-text-primary">Sensitive</span>
            </label>
            <ActionButton type="submit" disabled={busy}>
              Create
            </ActionButton>
          </form>
        </article>
      ) : null}

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Namespace</span>
          <select
            value={namespace}
            onChange={(event) => setNamespace(event.target.value)}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
          >
            <option value="">All</option>
            <option value="platform">platform</option>
            <option value="agency">agency</option>
            <option value="customer">customer</option>
          </select>
        </label>
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Module prefix</span>
          <input
            value={module}
            onChange={(event) => setModule(event.target.value)}
            placeholder="agency"
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
          />
        </label>
        <label className="m-0 flex items-end gap-2 pb-2 font-normal">
          <input
            type="checkbox"
            checked={sensitiveOnly}
            onChange={(event) => setSensitiveOnly(event.target.checked)}
          />
          <span className="text-body text-text-primary">Sensitive only</span>
        </label>
      </div>

      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <h2 className="m-0 mb-3 text-section text-text-primary">
          Catalog
          <span className="ml-2 text-body font-normal text-text-muted">
            ({permissions.length})
          </span>
        </h2>
        {loading && permissions.length === 0 ? (
          <TableSkeleton
            headers={["Code", "Namespace", "Description", "Flags"]}
            rows={8}
          />
        ) : permissions.length === 0 ? (
          <p className="m-0 text-body text-text-muted">No permissions match filters.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Code</th>
                  <th className="border-0 px-2 py-2 text-left">Namespace</th>
                  <th className="border-0 px-2 py-2 text-left">Description</th>
                  <th className="border-0 px-2 py-2 text-left">Flags</th>
                </tr>
              </thead>
              <tbody>
                {permissions.map((row) => (
                  <tr key={row.id} className="hover:bg-canvas">
                    <td className="px-2 py-3 font-mono text-body text-text-primary">{row.code}</td>
                    <td className="px-2 py-3 text-text-secondary">{row.namespace}</td>
                    <td className="px-2 py-3 text-text-secondary">{row.description || "—"}</td>
                    <td className="px-2 py-3">
                      <div className="flex flex-wrap gap-1.5">
                        {row.is_sensitive ? (
                          <StatusBadge tone="danger">sensitive</StatusBadge>
                        ) : null}
                        {row.is_custom ? (
                          <StatusBadge tone="warning">custom</StatusBadge>
                        ) : (
                          <StatusBadge tone="neutral">catalog</StatusBadge>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-4">
          <ApiNote>
            Sync inserts missing catalog codes and never deletes. Custom permissions are marked
            is_custom. Authorization always remains server-side.
          </ApiNote>
        </div>
      </article>
    </section>
  );
}
