import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { ListRowsSkeleton } from "@/components/ui/ListRowSkeleton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { toAppPath } from "@/nav";
import { useAgencyNumbers } from "./hooks/useAgencyNumbers";
import type { PhoneNumberRecord } from "./types";

type Tab = "inventory" | "search" | "assign" | "configure" | "release";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "available" || value === "assigned") return "success";
  if (value === "reserved" || value === "releasing") return "warning";
  if (value === "released") return "danger";
  return "neutral";
}

function statusLabel(status?: string): string {
  const value = (status ?? "").toLowerCase();
  if (value === "assigned") return "Active";
  return status || "—";
}

function formatCapabilities(capabilities?: string[]): string {
  if (!capabilities?.length) return "—";
  return capabilities.join(", ");
}

function formatMetaLine(parts: Array<string | null | undefined>): string {
  return parts.filter(Boolean).join(" · ");
}

function reservationSecondsLeft(expiresAt?: string | null): number | null {
  if (!expiresAt) return null;
  const ms = Date.parse(expiresAt) - Date.now();
  if (Number.isNaN(ms)) return null;
  return Math.max(0, Math.floor(ms / 1000));
}

function formatCountdown(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function NumberMetaBlock({
  row,
  currency = "USD",
}: {
  row: Pick<
    PhoneNumberRecord,
    | "country"
    | "area"
    | "provider"
    | "capabilities"
    | "monthly_cost_minor"
    | "currency"
    | "status"
    | "reserved_until"
  > & { provider?: string };
  currency?: string;
}) {
  return (
    <div className="text-sm text-text-muted">
      <p className="m-0">
        {formatMetaLine([
          row.provider,
          row.country,
          row.area,
          formatCapabilities(row.capabilities),
          `${formatMoneyMinor(row.monthly_cost_minor ?? 0, row.currency || currency)}/mo`,
        ])}
      </p>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        {row.status ? (
          <StatusBadge tone={statusTone(row.status)}>{statusLabel(row.status)}</StatusBadge>
        ) : null}
        {row.reserved_until ? (
          <span className="text-xs text-text-secondary">Until {row.reserved_until}</span>
        ) : null}
      </div>
    </div>
  );
}

export function AgencyNumbersScreen() {
  const navigate = useNavigate();
  const {
    assigned,
    assignments,
    inventory,
    offers,
    customers,
    agents,
    lastReservation,
    clearReservation,
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
    searchCapability,
    setSearchCapability,
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
  const [localPreview, setLocalPreview] = useState("");
  const [nowTick, setNowTick] = useState(() => Date.now());

  const agentOptions = useMemo(() => {
    if (!customerFilter) return agents;
    return agents.filter((row) => row.customer_id === customerFilter);
  }, [agents, customerFilter]);

  const reserveAgent = agents.find((row) => row.id === reserveAgentId) ?? null;
  const reservationNumber =
    inventory.find((row) => row.id === lastReservation?.number_id) ||
    assigned.find((row) => row.id === lastReservation?.number_id) ||
    null;

  const secondsLeft = useMemo(() => {
    void nowTick;
    return reservationSecondsLeft(lastReservation?.expires_at);
  }, [lastReservation?.expires_at, nowTick]);
  const reservationExpired = Boolean(lastReservation) && secondsLeft === 0;

  useEffect(() => {
    if (!lastReservation?.expires_at) return;
    const id = window.setInterval(() => setNowTick(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [lastReservation?.expires_at]);

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
      setLocalPreview("");
      setTab("assign");
    } catch {
      /* hook message */
    }
  }

  async function onAssign(confirm: boolean) {
    if (!lastReservation?.id) return;
    if (!confirm) {
      // Backend rejects confirm=false with assign_confirmation_required — preview is local only.
      const match = reservationNumber;
      const cost = match?.monthly_cost_minor;
      setLocalPreview(
        cost == null
          ? "Local estimate only — confirm assign bills this customer's active subscription for the number's monthly cost. Backend does not run a dry-run."
          : `Local estimate only: ${formatMoneyMinor(cost, match?.currency || "USD")}/mo. Customer must already have an active plan subscription. Confirm assign to create the invoice.`,
      );
      return;
    }
    setLocalPreview("");
    try {
      await assignReservation(lastReservation.id, true);
      setTab("inventory");
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
    { id: "search", label: "Search" },
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
            Search → reserve → assign → release · AG4 / Q-002
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

      <div className="mb-4 rounded-xl border border-border-default bg-surface-muted px-4 py-3 text-sm text-text-secondary">
        <strong className="font-semibold text-text-primary">Flow:</strong> Platform stocks
        inventory → Agency searches and reserves (10 min) with an agent → Confirm assign creates
        the customer invoice → Release when done. Provider offers are informational only until
        Super Admin stocks them.
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <ActionButton
            key={item.id}
            variant={tab === item.id ? "secondary" : "outline"}
            onClick={() => setTab(item.id)}
          >
            {item.label}
            {item.id === "assign" && lastReservation ? " · pending" : ""}
          </ActionButton>
        ))}
      </div>

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <FormField
          label="Search inventory"
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
          <option value="">Select agent (required to reserve)</option>
          {agentOptions.map((row) => (
            <option key={row.id} value={row.id}>
              {row.display_name || row.id.slice(0, 8)}
              {row.customer_id ? ` · ${customerName(row.customer_id)}` : ""}
            </option>
          ))}
        </FormSelect>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            {tab === "search" ? "Search results" : "Assigned numbers"}
          </h2>
          {tab === "search" ? (
            <div className="grid gap-4">
              <form
                className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
                onSubmit={(event) => void onSearch(event)}
              >
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
                <FormSelect
                  label="Capability"
                  name="capability"
                  value={searchCapability}
                  onChange={(event) => setSearchCapability(event.target.value)}
                >
                  <option value="voice">voice</option>
                  <option value="sms">sms</option>
                  <option value="mms">mms</option>
                </FormSelect>
                <div className="flex items-end">
                  <ActionButton type="submit" disabled={busy}>
                    Search
                  </ActionButton>
                </div>
              </form>
              {!reserveAgentId ? (
                <p className="m-0 text-sm text-text-secondary" role="status">
                  Select an agent above before reserving. The agent&apos;s customer must be Active
                  with a plan subscription for assign to succeed.
                </p>
              ) : null}
              {loading && inventory.length === 0 && offers.length === 0 ? (
                <ListRowsSkeleton rows={6} />
              ) : (
                <>
                  <div>
                    <h3 className="m-0 mb-2 text-sm font-semibold text-text-primary">
                      Platform inventory
                    </h3>
                    {!inventory.length ? (
                      <p className="m-0 text-body text-text-muted">
                        No inventory matches. Ask Super Admin to stock or purchase DIDs on Platform
                        Numbers first.
                      </p>
                    ) : (
                      <ul className="m-0 grid list-none gap-2 p-0">
                        {inventory.map((row) => (
                          <li
                            key={row.id}
                            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                          >
                            <div>
                              <p className="m-0 font-medium text-text-primary">{row.e164}</p>
                              <NumberMetaBlock row={row} />
                            </div>
                            <ActionButton
                              disabled={
                                busy ||
                                !reserveAgentId ||
                                (row.status ?? "").toLowerCase() === "reserved"
                              }
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
                            <NumberMetaBlock
                              row={{
                                provider: row.provider,
                                country: row.country,
                                area: row.area,
                                capabilities: row.capabilities,
                                monthly_cost_minor: row.monthly_cost_minor,
                              }}
                            />
                          </li>
                        ))}
                      </ul>
                    )}
                    <ApiNote>
                      Offers cannot be bought from Agency UI (Q-002). Platform must stock/purchase
                      first; then reserve from inventory rows (AG4-001 / VKT-079).
                    </ApiNote>
                  </div>
                </>
              )}
            </div>
          ) : loading && assigned.length === 0 ? (
            <ListRowsSkeleton rows={8} />
          ) : !assigned.length ? (
            <p className="m-0 text-body text-text-muted">
              No assigned numbers yet. Use Search to reserve inventory, then Assign.
            </p>
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
                      <StatusBadge tone={statusTone(row.status)}>
                        {statusLabel(row.status)}
                      </StatusBadge>
                    </div>
                    <p className="m-0 mt-1 text-sm text-text-muted">
                      {formatMetaLine([
                        row.provider,
                        customerName(row.assigned_customer_id),
                        agentName(row.assigned_agent_id),
                      ])}
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
                  Reserve a number from Search first. Reservations expire after 10 minutes.
                </p>
              ) : (
                <>
                  <dl className="m-0 grid gap-2 rounded-lg border border-border-default bg-surface-muted px-3 py-3 text-sm">
                    <div>
                      <dt className="text-text-muted">Number</dt>
                      <dd className="m-0 font-medium text-text-primary">
                        {reservationNumber?.e164 || lastReservation.number_id?.slice(0, 8) || "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Agent / customer</dt>
                      <dd className="m-0 text-text-primary">
                        {agentName(lastReservation.agent_id)} ·{" "}
                        {customerName(
                          lastReservation.customer_id || reserveAgent?.customer_id,
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Monthly cost</dt>
                      <dd className="m-0 text-text-primary">
                        {reservationNumber
                          ? formatMoneyMinor(
                              reservationNumber.monthly_cost_minor ?? 0,
                              reservationNumber.currency || "USD",
                            )
                          : "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Hold expires</dt>
                      <dd className="m-0 text-text-primary">
                        {lastReservation.expires_at || "—"}
                        {secondsLeft != null && !reservationExpired ? (
                          <span
                            className={
                              secondsLeft <= 60
                                ? " ml-2 font-semibold text-danger"
                                : " ml-2 text-text-secondary"
                            }
                          >
                            ({formatCountdown(secondsLeft)} left)
                          </span>
                        ) : null}
                      </dd>
                    </div>
                  </dl>
                  {reservationExpired ? (
                    <div className="grid gap-2">
                      <p className="m-0 text-body text-danger" role="alert">
                        Reservation expired. Return to Search and reserve again.
                      </p>
                      <ActionButton
                        variant="outline"
                        onClick={() => {
                          clearReservation();
                          setLocalPreview("");
                          setTab("search");
                        }}
                      >
                        Back to Search
                      </ActionButton>
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      <ActionButton
                        variant="outline"
                        disabled={busy}
                        onClick={() => void onAssign(false)}
                      >
                        Preview cost (local)
                      </ActionButton>
                      <ActionButton disabled={busy} onClick={() => void onAssign(true)}>
                        Confirm assign
                      </ActionButton>
                    </div>
                  )}
                  {localPreview && !reservationExpired ? (
                    <p className="m-0 text-body text-text-secondary" role="status">
                      {localPreview}
                    </p>
                  ) : null}
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
                        {row.invoice_id ? ` · invoice ${row.invoice_id.slice(0, 8)}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <ApiNote>
                Confirm assign binds the DID to one agent under its customer and invoices the
                monthly cost (AG4-002). Customer needs an active subscription.
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
                <p className="m-0 text-body text-text-muted">
                  Select an assigned number for context, or open Agents / Transfers directly.
                </p>
              )}
              <p className="m-0 text-body text-text-secondary">
                Inbound routing, voice settings, and fallback live on the{" "}
                <strong className="font-semibold text-text-primary">agent</strong>. Transfer
                destinations and queues live under{" "}
                <strong className="font-semibold text-text-primary">Transfers</strong>. There is no
                separate number-configure API in V1 (AG4-003 deferred).
              </p>
              <div className="flex flex-wrap gap-2">
                <ActionButton
                  variant="secondary"
                  onClick={() => navigate(toAppPath("/agents"))}
                >
                  Open Agents
                </ActionButton>
                <ActionButton
                  variant="outline"
                  onClick={() => navigate(toAppPath("/transfers"))}
                >
                  Open Transfers
                </ActionButton>
              </div>
              <ApiNote>
                Configure voice/CID/tools on Agents; transfer targets on Transfers — not on the
                phone number record.
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
                    Releasing {selected.e164} removes assignment from{" "}
                    {customerName(selected.assigned_customer_id)} /{" "}
                    {agentName(selected.assigned_agent_id)}. Inbound calls to this DID will fail
                    until reassigned. Type RELEASE to confirm.
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
                        {statusLabel(selected.status)}
                      </StatusBadge>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Provider</dt>
                    <dd className="m-0 text-text-primary">{selected.provider || "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Country / area</dt>
                    <dd className="m-0 text-text-primary">
                      {formatMetaLine([selected.country, selected.area]) || "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Capabilities</dt>
                    <dd className="m-0 text-text-primary">
                      {formatCapabilities(selected.capabilities)}
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
                  {selected.reserved_until ? (
                    <div>
                      <dt className="text-text-muted">Reserved until</dt>
                      <dd className="m-0 text-text-primary">{selected.reserved_until}</dd>
                    </div>
                  ) : null}
                </dl>
              )}
              <div className="flex flex-wrap gap-2">
                <ActionButton variant="outline" onClick={() => setTab("search")}>
                  Search inventory
                </ActionButton>
                {selected ? (
                  <ActionButton variant="outline" onClick={() => setTab("release")}>
                    Release…
                  </ActionButton>
                ) : null}
              </div>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
