import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { customerCreateHref, customerDetailHref } from "@/features/customers/lib/routes";
import { customerStatusTone } from "@/features/customers/lib/status";
import { usePlatformCustomerList } from "@/features/customers/hooks/usePlatformCustomerList";
import { CUSTOMER_STATUSES } from "@/features/customers/types";

export function PlatformCustomersScreen() {
  const navigate = useNavigate();
  const [agencyFilter, setAgencyFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query), 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  const { customers, agencies, agencyName, error, loading } = usePlatformCustomerList({
    agencyId: agencyFilter,
    status: statusFilter,
    query: debouncedQuery,
  });

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Customers
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Global customer directory across agencies.
          </p>
        </div>
        <ActionButton onClick={() => navigate(customerCreateHref())}>Create customer</ActionButton>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}

      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <div className="mb-4 grid gap-3 lg:grid-cols-3">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search name or id…"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Agency</span>
            <select
              value={agencyFilter}
              onChange={(event) => setAgencyFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All agencies</option>
              {agencies.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.display_name || row.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Status</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All statuses</option>
              {CUSTOMER_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
        </div>

        <h2 className="m-0 mb-3 text-section text-text-primary">
          Directory
          <span className="ml-2 text-body font-normal text-text-muted">({customers.length})</span>
        </h2>

        {loading ? (
          <p className="m-0 text-body text-text-muted" role="status">
            Loading customers…
          </p>
        ) : customers.length === 0 ? (
          <div className="grid gap-3 py-12 text-center">
            <p className="m-0 text-body text-text-muted">No customers match this view.</p>
            <div>
              <ActionButton variant="outline" onClick={() => navigate(customerCreateHref())}>
                Create the first customer
              </ActionButton>
            </div>
          </div>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Customer</th>
                  <th className="border-0 px-2 py-2 text-left">Agency</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Updated</th>
                  <th className="border-0 px-2 py-2 text-left">
                    <span className="sr-only">Open</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {customers.map((row) => (
                  <tr
                    key={row.id}
                    className="cursor-pointer hover:bg-canvas"
                    onClick={() => navigate(customerDetailHref(row.id))}
                  >
                    <td className="px-2 py-3">
                      <p className="m-0 font-semibold text-text-primary">
                        {row.display_name || row.id.slice(0, 8)}
                      </p>
                      <p className="m-0 text-body-sm text-text-muted">{row.id.slice(0, 8)}</p>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{agencyName(row.agency_id)}</td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={customerStatusTone(row.status)}>
                        {row.status || "unknown"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      {row.updated_at || row.created_at
                        ? new Date(String(row.updated_at || row.created_at)).toLocaleDateString()
                        : "—"}
                    </td>
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
