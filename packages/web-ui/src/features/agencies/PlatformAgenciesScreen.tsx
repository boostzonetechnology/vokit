import { useNavigate } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TableSkeleton } from "@/components/ui/TableSkeleton";
import { usePlatformAgencyList } from "@/features/agencies/hooks/usePlatformAgencyList";
import { resolveCommissionDisplay } from "@/features/agencies/lib/commission";
import { agencyCreateHref, agencyDetailHref } from "@/features/agencies/lib/routes";
import {
  agencyStatusTone,
  formatAgencyStatus,
} from "@/features/agencies/lib/status";
import { AGENCY_STATUS_FILTERS } from "@/features/agencies/types";

export function PlatformAgenciesScreen() {
  const navigate = useNavigate();
  const {
    agencies,
    error,
    loading,
    statusFilter,
    nameQuery,
    setStatusFilter,
    setNameQuery,
  } = usePlatformAgencyList();

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agencies
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Super Admin directory — search by name, filter by status, open an agency to manage
            profile, commission, capabilities, finance, and notes.
          </p>
        </div>
        <ActionButton onClick={() => navigate(agencyCreateHref())}>Create agency</ActionButton>
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
            <span className="ml-2 text-body font-normal text-text-muted">({agencies.length})</span>
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
                {AGENCY_STATUS_FILTERS.map((status) => (
                  <option key={status} value={status}>
                    {formatAgencyStatus(status)}
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 min-w-[220px] flex-1 font-normal">
              <span className="sr-only">Search agencies</span>
              <input
                value={nameQuery}
                onChange={(event) => setNameQuery(event.target.value)}
                placeholder="Search display or legal name…"
                className="w-full rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
          </div>
        </div>

        {loading && agencies.length === 0 ? (
          <TableSkeleton
            headers={["Agency", "Status", "Database", "Commission", "Currency"]}
            rows={8}
          />
        ) : agencies.length === 0 ? (
          <div className="grid gap-3 py-12 text-center">
            <p className="m-0 text-body text-text-muted">No agencies match this view.</p>
            <div>
              <ActionButton variant="outline" onClick={() => navigate(agencyCreateHref())}>
                Create the first agency
              </ActionButton>
            </div>
          </div>
        ) : (
          <div className="overflow-auto rounded-xl border border-border-default">
            <table className="min-w-full">
              <thead>
                <tr className="bg-canvas text-label uppercase text-text-muted">
                  <th className="border-0 px-3 py-2.5 text-left">Agency</th>
                  <th className="border-0 px-3 py-2.5 text-left">Status</th>
                  <th className="border-0 px-3 py-2.5 text-left">Database</th>
                  <th className="border-0 px-3 py-2.5 text-left">Commission</th>
                  <th className="border-0 px-3 py-2.5 text-left">Currency</th>
                  <th className="border-0 px-3 py-2.5 text-left">
                    <span className="sr-only">Open</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {agencies.map((row) => {
                  const commission = resolveCommissionDisplay(row);
                  return (
                    <tr
                      key={row.id}
                      className="cursor-pointer border-t border-border-default hover:bg-canvas"
                      onClick={() => navigate(agencyDetailHref(row.id))}
                    >
                      <td className="px-3 py-3">
                        <p className="m-0 font-semibold text-text-primary">
                          {row.display_name || row.legal_name || "Untitled agency"}
                        </p>
                        <p className="m-0 text-body-sm text-text-muted">
                          {row.legal_name && row.legal_name !== row.display_name
                            ? row.legal_name
                            : "—"}
                        </p>
                      </td>
                      <td className="px-3 py-3">
                        <StatusBadge tone={agencyStatusTone(row.status)}>
                          {formatAgencyStatus(row.status)}
                        </StatusBadge>
                      </td>
                      <td className="px-3 py-3 text-text-secondary">
                        <p className="m-0">{row.database?.name || "—"}</p>
                        <p className="m-0 text-body-sm text-text-muted">
                          {formatAgencyStatus(row.database?.status || row.tenant_status)}
                        </p>
                      </td>
                      <td className="px-3 py-3 text-text-secondary">
                        <p className="m-0">{commission.liveLabel}</p>
                        {commission.isScheduled ? (
                          <p className="m-0 text-body-sm text-text-muted">
                            → {commission.scheduledLabel}
                          </p>
                        ) : null}
                      </td>
                      <td className="px-3 py-3 text-text-secondary">{row.currency || "USD"}</td>
                      <td className="px-3 py-3 text-right">
                        <span className="text-body-sm font-semibold text-text-brand">Open →</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
