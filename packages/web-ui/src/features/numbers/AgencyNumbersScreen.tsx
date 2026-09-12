import { FormEvent, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyNumbers } from "./hooks/useAgencyNumbers";

type Tab = "inventory" | "search" | "assign" | "configure" | "release";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "available" || value === "assigned") return "success";
  if (value === "reserved") return "warning";
  if (value === "released") return "danger";
  return "neutral";
}

export function AgencyNumbersScreen() {
  const {
    assigned,
    assignments,
    inventory,
    offers,
    customers,
    agents,
    lastReservation,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    customerFilter,
    setCustomerFilter,
    searchCountry,
    setSearchCountry,
    searchArea,
    setSearchArea,
    customerName,
    agentName,
    reload,
    searchNumbers,
    reserveNumber,
    assignReservation,
    releaseNumber,
  } = useAgencyNumbers();

  const [tab, setTab] = useState<Tab>("inventory");
  const [reserveAgentId, setReserveAgentId] = useState("");
  const [releaseConfirm, setReleaseConfirm] = useState("");

  const agentOptions = useMemo(() => {
    if (!customerFilter) return agents;
    return agents.filter((row) => row.customer_id === customerFilter);
  }, [agents, customerFilter]);

  async function onSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await searchNumbers();
    } catch {
      /* hook message */
    }
  }

  async function onReserve(numberId: string) {
    if (!reserveAgentId) {
      return;
    }
    try {
      await reserveNumber(numberId, reserveAgentId);
      setTab("assign");
    } catch {
      /* hook message */
    }
  }

  async function onAssign(confirm: boolean) {
    if (!lastReservation?.id) return;
    try {
      await assignReservation(lastReservation.id, confirm);
      if (confirm) setTab("inventory");
    } catch {
      /* hook message */
    }
  }

  async function onRelease() {
    if (!selectedId || releaseConfirm !== "RELEASE") return;
    try {
      await releaseNumber(selectedId);
      setReleaseConfirm("");
      setTab("inventory");
    } catch {
      /* hook message */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "inventory", label: "Inventory" },
    { id: "search", label: "Search / buy" },
    { id: "assign", label: "Assign" },
    { id: "configure", label: "Configure" },
    { id: "release", label: "Release" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Phone numbers
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Search, assign, configure, release · AG4
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
        <p className="mb-4 text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <ActionButton
            key={item.id}
            variant={tab === item.id ? "secondary" : "outline"}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </ActionButton>
        ))}
      </div>

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <FormField
          label="Search"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="E.164, agent, status…"
        />
        <FormSelect
          label="Customer filter"
          name="customer_filter"
          value={customerFilter}
          onChange={(event) => setCustomerFilter(event.target.value)}
        >
          <option value="">All customers</option>
          {customers.map((row) => (
            <option key={row.id} value={row.id}>
              {row.display_name || row.id.slice(0, 8)}
            </option>
          ))}
        </FormSelect>
        <FormSelect
          label="Agent for reserve"
          name="reserve_agent"
          value={reserveAgentId}
          onChange={(event) => setReserveAgentId(event.target.value)}
        >
          <option value="">Select agent</option>
          {agentOptions.map((row) => (
            <option key={row.id} value={row.id}>
              {row.display_name || row.id.slice(0, 8)}
            </option>
          ))}
        </FormSelect>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            {tab === "search" ? "Search results" : "Assigned numbers"}
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted" role="status">
              Loading…
            </p>
          ) : tab === "search" ? (
            <div className="grid gap-4">
              <form className="grid gap-3 sm:grid-cols-3" onSubmit={(event) => void onSearch(event)}>
                <FormField
                  label="Country"
                  name="country"
                  value={searchCountry}
                  onChange={(event) => setSearchCountry(event.target.value)}
                />
                <FormField
                  label="Area"
                  name="area"
                  value={searchArea}
                  onChange={(event) => setSearchArea(event.target.value)}
                />
                <div className="flex items-end">
                  <ActionButton type="submit" disabled={busy}>
                    Search
                  </ActionButton>
                </div>
              </form>
              <div>
                <h3 className="m-0 mb-2 text-sm font-semibold text-text-primary">
                  Platform inventory
                </h3>
                {!inventory.length ? (
                  <p className="m-0 text-body text-text-muted">No inventory matches.</p>
                ) : (
                  <ul className="m-0 grid list-none gap-2 p-0">
                    {inventory.map((row) => (
                      <li
                        key={row.id}
                        className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                      >
                        <div>
                          <p className="m-0 font-medium text-text-primary">{row.e164}</p>
                          <p className="m-0 text-sm text-text-muted">
                            {row.country}
                            {row.area ? ` · ${row.area}` : ""} ·{" "}
                            {formatMoneyMinor(row.monthly_cost_minor ?? 0, row.currency || "USD")}
                            /mo
                          </p>
                        </div>
                        <ActionButton
                          disabled={busy || !reserveAgentId}
                          onClick={() => void onReserve(row.id)}
                        >
                          Reserve
                        </ActionButton>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <h3 className="m-0 mb-2 text-sm font-semibold text-text-primary">
                  Provider offers
                </h3>
                {!offers.length ? (
                  <p className="m-0 text-body text-text-muted">No provider offers returned.</p>
                ) : (
                  <ul className="m-0 grid list-none gap-2 p-0">
                    {offers.map((row) => (
                      <li
                        key={`${row.e164}-${row.provider}`}
                        className="rounded-lg border border-border-default px-3 py-2"
                      >
                        <p className="m-0 font-medium text-text-primary">{row.e164}</p>
                        <p className="m-0 text-sm text-text-muted">
                          {row.provider} ·{" "}
                          {formatMoneyMinor(row.monthly_cost_minor ?? 0, "USD")}/mo
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
                <ApiNote>
                  Provider offers are informational until stocked/purchased into inventory. Reserve
                  from inventory rows to start assign (AG4-001).
                </ApiNote>
              </div>
            </div>
          ) : !assigned.length ? (
            <p className="m-0 text-body text-text-muted">No assigned numbers yet.</p>
          ) : (
            <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
              {assigned.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                      selectedId === row.id
                        ? "border-border-brand bg-surface-muted"
                        : "border-border-default bg-surface hover:bg-surface-muted"
                    }`}
                    onClick={() => setSelectedId(row.id)}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-text-primary">{row.e164}</span>
                      <StatusBadge tone={statusTone(row.status)}>{row.status || "—"}</StatusBadge>
                    </div>
                    <p className="m-0 mt-1 text-sm text-text-muted">
                      {customerName(row.assigned_customer_id)} · {agentName(row.assigned_agent_id)}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          {tab === "assign" ? (
            <div className="grid gap-3">
              <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">
                Assign reservation
              </h2>
              {!lastReservation ? (
                <p className="m-0 text-body text-text-muted">
                  Reserve a number from Search / buy first.
                </p>
              ) : (
                <>
                  <p className="m-0 text-body text-text-muted">
                    Reservation {lastReservation.id.slice(0, 8)} · agent{" "}
                    {agentName(lastReservation.agent_id)} · expires{" "}
                    {lastReservation.expires_at || "—"}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => void onAssign(false)}
                    >
                      Preview cost
                    </ActionButton>
                    <ActionButton disabled={busy} onClick={() => void onAssign(true)}>
                      Confirm assign
                    </ActionButton>
                  </div>
                </>
              )}
              <h3 className="m-0 mt-2 text-sm font-semibold text-text-primary">
                Recent assignments
              </h3>
              {!assignments.length ? (
                <p className="m-0 text-body text-text-muted">No assignment history.</p>
              ) : (
                <ul className="m-0 grid list-none gap-2 p-0">
                  {assignments.slice(0, 8).map((row) => (
                    <li
                      key={row.id}
                      className="rounded-lg border border-border-default px-3 py-2 text-sm"
                    >
                      <span className="font-medium text-text-primary">{row.e164}</span>
                      <span className="text-text-muted">
                        {" "}
                        · {row.status} · {agentName(row.agent_id)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <ApiNote>
                Assign binds the DID to a compatible agent under its customer (AG4-002).
              </ApiNote>
            </div>
          ) : tab === "configure" ? (
            <div className="grid gap-3">
              <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">
                Number configuration
              </h2>
              {selected ? (
                <p className="m-0 text-body text-text-muted">
                  Selected {selected.e164} · agent {agentName(selected.assigned_agent_id)}
                </p>
              ) : (
                <p className="m-0 text-body text-text-muted">Select an assigned number.</p>
              )}
              <ApiNote>
                Inbound routing, lawful caller ID, transfer and fallback are configured on the
                agent and transfer destinations today. A dedicated number-configure API is not
                exposed yet (AG4-003).
              </ApiNote>
            </div>
          ) : tab === "release" ? (
            <div className="grid gap-3">
              <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">Release number</h2>
              {!selected ? (
                <p className="m-0 text-body text-text-muted">Select an assigned number to release.</p>
              ) : (
                <>
                  <p className="m-0 text-body text-danger" role="alert">
                    Releasing {selected.e164} removes assignment. Inbound calls to this DID will
                    fail until reassigned. Type RELEASE to confirm.
                  </p>
                  <FormField
                    label="Confirmation"
                    name="release_confirm"
                    value={releaseConfirm}
                    onChange={(event) => setReleaseConfirm(event.target.value)}
                    placeholder="RELEASE"
                  />
                  <ActionButton
                    disabled={busy || releaseConfirm !== "RELEASE"}
                    onClick={() => void onRelease()}
                  >
                    Confirm release
                  </ActionButton>
                </>
              )}
              <ApiNote>AG4-004 requires explicit confirmation and impact warning.</ApiNote>
            </div>
          ) : (
            <div className="grid gap-3">
              <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">Number detail</h2>
              {!selected ? (
                <p className="m-0 text-body text-text-muted">Select a number from the list.</p>
              ) : (
                <dl className="m-0 grid gap-2 text-sm">
                  <div>
                    <dt className="text-text-muted">E.164</dt>
                    <dd className="m-0 font-medium text-text-primary">{selected.e164}</dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Status</dt>
                    <dd className="m-0">
                      <StatusBadge tone={statusTone(selected.status)}>
                        {selected.status || "—"}
                      </StatusBadge>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Customer</dt>
                    <dd className="m-0 text-text-primary">
                      {customerName(selected.assigned_customer_id)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Agent</dt>
                    <dd className="m-0 text-text-primary">
                      {agentName(selected.assigned_agent_id)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Monthly cost</dt>
                    <dd className="m-0 text-text-primary">
                      {formatMoneyMinor(
                        selected.monthly_cost_minor ?? 0,
                        selected.currency || "USD",
                      )}
                    </dd>
                  </div>
                </dl>
              )}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
