import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { agencyCreateHref, agencyDetailHref } from "@/features/agencies/lib/routes";
import { agencyStatusTone, bpsToPercent } from "@/features/agencies/lib/status";
import { usePlatformAgencyList } from "@/features/agencies/hooks/usePlatformAgencyList";

export function PlatformAgenciesScreen() {
  const navigate = useNavigate();
  const { agencies, error, loading } = usePlatformAgencyList();
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return agencies.filter((row) => {
      if (statusFilter && (row.status || "").toLowerCase() !== statusFilter) return false;
      if (!q) return true;
      return [row.display_name, row.legal_name, row.status, row.id, row.database?.name]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [agencies, query, statusFilter]);

  const statuses = useMemo(() => {
    const set = new Set<string>();
    for (const row of agencies) {
      if (row.status) set.add(row.status);
    }
    return Array.from(set).sort();
  }, [agencies]);

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agencies
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Directory of agency tenants. Open an agency to manage profile, commission, status, and
            database metadata.
          </p>
        </div>
        <ActionButton onClick={() => navigate(agencyCreateHref())}>
          Create agency
        </ActionButton>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}

      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="m-0 text-section text-text-primary">
            Agency directory
            <span className="ml-2 text-body font-normal text-text-muted">({filtered.length})</span>
          </h2>
          <div className="flex flex-wrap gap-2">
            <label className="m-0 font-normal">
              <span className="sr-only">Filter by status</span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">All statuses</option>
                {statuses.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 min-w-[220px] flex-1 font-normal">
              <span className="sr-only">Search agencies</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search name, status, or database…"
                className="w-full rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
          </div>
        </div>

        {loading ? (
          <p className="m-0 text-body text-text-muted" role="status">
            Loading agencies…
          </p>
        ) : filtered.length === 0 ? (
          <div className="grid gap-3 py-12 text-center">
            <p className="m-0 text-body text-text-muted">No agencies match this view.</p>
            <div>
              <ActionButton
                variant="outline"
                onClick={() => navigate(agencyCreateHref())}
              >
                Create the first agency
              </ActionButton>
            </div>
          </div>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Agency</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Database</th>
                  <th className="border-0 px-2 py-2 text-left">Commission</th>
                  <th className="border-0 px-2 py-2 text-left">Currency</th>
                  <th className="border-0 px-2 py-2 text-left">
                    <span className="sr-only">Open</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr
                    key={row.id}
                    className="cursor-pointer hover:bg-canvas"
                    onClick={() => {
                      navigate(agencyDetailHref(row.id));
                    }}
                  >
                    <td className="px-2 py-3">
                      <p className="m-0 font-semibold text-text-primary">
                        {row.display_name || row.id.slice(0, 8)}
                      </p>
                      <p className="m-0 text-body-sm text-text-muted">{row.legal_name || "—"}</p>
                    </td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={agencyStatusTone(row.status)}>
                        {row.status || "unknown"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      <p className="m-0">{row.database?.name || "—"}</p>
                      <p className="m-0 text-body-sm text-text-muted">
                        {row.database?.status || row.tenant_status || "—"}
                      </p>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      {bpsToPercent(row.commission_rate_bps)}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.currency || "USD"}</td>
                    <td className="px-2 py-3 text-right">
                      <span className="text-body-sm font-semibold text-text-brand">Open →</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
