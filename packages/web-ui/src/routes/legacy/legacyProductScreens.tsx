import { FormEvent, useCallback, useEffect, useState } from "react";

import { Portal, apiGet, apiSend, isApiError } from "@/api";

type Row = Record<string, unknown>;

function cell(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function asList(data: unknown): Row[] {
  if (Array.isArray(data)) return data as Row[];
  if (data && typeof data === "object") {
    const record = data as Row;
    for (const key of ["assigned", "inventory", "assignments", "items", "results", "lots"]) {
      if (Array.isArray(record[key])) return record[key] as Row[];
    }
    return [record];
  }
  return [];
}

function useRows(path: string | null) {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const refresh = useCallback(() => setReload((n) => n + 1), []);

  useEffect(() => {
    if (!path) {
      setRows([]);
      return;
    }
    let active = true;
    apiGet<unknown>(path)
      .then((data) => {
        if (active) {
          setRows(asList(data));
          setError("");
        }
      })
      .catch((cause) => {
        if (active) {
          setError(isApiError(cause) ? cause.message : "Load failed.");
          setRows([]);
        }
      });
    return () => {
      active = false;
    };
  }, [path, reload]);

  return { rows, error, refresh, setError };
}

function Message({ value }: { value: string }) {
  if (!value) return null;
  return (
    <p className={value.toLowerCase().includes("fail") || value.toLowerCase().includes("error") ? "text-danger" : "text-text-secondary"} role="status">
      {value}
    </p>
  );
}

function DataTable({
  rows,
  columns,
  empty,
  onSelect,
}: {
  rows: Row[];
  columns: { key: string; label: string }[];
  empty: string;
  onSelect?: (row: Row) => void;
}) {
  if (!rows.length) {
    return <p className="rounded-lg border border-dashed border-border-strong bg-surface p-6 text-text-muted">{empty}</p>;
  }
  return (
    <div className="overflow-auto rounded-lg border border-border-default bg-surface">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={String(row.id ?? index)}
              className={onSelect ? "cursor-pointer hover:bg-brand-subtle" : undefined}
              onClick={onSelect ? () => onSelect(row) : undefined}
            >
              {columns.map((col) => (
                <td key={col.key}>{cell(row[col.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AgenciesScreen() {
  const { rows, error, refresh } = useRows("/api/v1/platform/agencies");
  const [message, setMessage] = useState("");
  const [selected, setSelected] = useState<Row | null>(null);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/api/v1/platform/agencies", "POST", {
        display_name: String(form.get("display_name") || ""),
        legal_name: String(form.get("legal_name") || ""),
        owner_email: String(form.get("owner_email") || ""),
        commission_rate_bps: Number(form.get("commission_rate_bps") || 0),
      });
      setMessage("Agency created — tenant DB allocated on the server.");
      event.currentTarget.reset();
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
    }
  }

  async function patchStatus(action: string) {
    if (!selected?.id) return;
    try {
      await apiSend(`/api/v1/platform/agencies/${selected.id}/status`, "POST", { action });
      setMessage(`Status action: ${action}`);
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Status update failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2>Agencies</h2>
      </div>
      <Message value={error || message} />
      <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
        <h3>Create agency</h3>
        <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void onCreate(e)}>
          <label>
            Display name
            <input name="display_name" required />
          </label>
          <label>
            Legal name
            <input name="legal_name" required />
          </label>
          <label>
            Owner email
            <input name="owner_email" type="email" required />
          </label>
          <label>
            Commission (bps)
            <input name="commission_rate_bps" type="number" min={0} max={10000} defaultValue={1500} />
          </label>
          <p className="col-span-full text-text-secondary">
            Database host/name/password are never collected here — allocated from server settings.
          </p>
          <button type="submit">Create</button>
        </form>
      </article>
      <DataTable
        rows={rows}
        columns={[
          { key: "display_name", label: "Name" },
          { key: "legal_name", label: "Legal" },
          { key: "status", label: "Agency" },
          { key: "tenant_status", label: "Tenant DB" },
          { key: "commission_rate_bps", label: "Commission bps" },
          { key: "id", label: "Id" },
        ]}
        empty="No agencies yet."
        onSelect={setSelected}
      />
      {selected ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>{cell(selected.display_name)}</h3>
          <dl className="grid gap-2">
            <div>
              <dt>Id</dt>
              <dd>{cell(selected.id)}</dd>
            </div>
            <div>
              <dt>Capabilities</dt>
              <dd>{cell(selected.capabilities)}</dd>
            </div>
          </dl>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => void patchStatus("suspend")}>
              Suspend
            </button>
            <button type="button" onClick={() => void patchStatus("activate")}>
              Activate
            </button>
          </div>
        </article>
      ) : null}
    </section>
  );
}

export function CustomersScreen({ portal }: { portal: Portal }) {
  const base = portal === "platform" ? "/api/v1/platform/customers" : "/api/v1/agency/customers";
  const { rows, error, refresh } = useRows(base);
  const [message, setMessage] = useState("");
  const [agencies, setAgencies] = useState<Row[]>([]);

  useEffect(() => {
    if (portal !== "platform") return;
    apiGet<Row[]>("/api/v1/platform/agencies")
      .then((data) => setAgencies(Array.isArray(data) ? data : []))
      .catch(() => setAgencies([]));
  }, [portal]);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const body: Row = {
      display_name: String(form.get("display_name") || ""),
      owner_email: String(form.get("owner_email") || "") || undefined,
      notes: String(form.get("notes") || "") || undefined,
      contact_name: String(form.get("contact_name") || "") || undefined,
      contact_email: String(form.get("contact_email") || "") || undefined,
      contact_phone: String(form.get("contact_phone") || "") || undefined,
      address: String(form.get("address") || "") || undefined,
    };
    if (portal === "platform") {
      body.agency_id = String(form.get("agency_id") || "");
    }
    try {
      await apiSend(base, "POST", body);
      setMessage("Customer created.");
      event.currentTarget.reset();
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2>Customers</h2>
      </div>
      <Message value={error || message} />
      <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
        <h3>Create customer</h3>
        <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void onCreate(e)}>
          {portal === "platform" ? (
            <label>
              Agency
              <select name="agency_id" required defaultValue="">
                <option value="" disabled>
                  Select agency
                </option>
                {agencies.map((a) => (
                  <option key={String(a.id)} value={String(a.id)}>
                    {cell(a.display_name)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <label>
            Business name
            <input name="display_name" required />
          </label>
          <label>
            Owner email
            <input name="owner_email" type="email" />
          </label>
          <label>
            Contact name
            <input name="contact_name" />
          </label>
          <label>
            Contact email
            <input name="contact_email" type="email" />
          </label>
          <label>
            Phone
            <input name="contact_phone" />
          </label>
          <label className="col-span-full">
            Address
            <input name="address" />
          </label>
          <label className="col-span-full">
            Notes
            <textarea name="notes" rows={2} />
          </label>
          <button type="submit">Create</button>
        </form>
      </article>
      <DataTable
        rows={rows}
        columns={[
          { key: "display_name", label: "Name" },
          { key: "status", label: "Status" },
          { key: "agency_id", label: "Agency" },
          { key: "id", label: "Id" },
        ]}
        empty="No customers yet."
      />
    </section>
  );
}

export function AgentsScreen({ portal }: { portal: Portal }) {
  const listPath =
    portal === "agency" ? "/api/v1/agency/agents" : "/api/v1/customer/agents";
  const { rows, error, refresh } = useRows(listPath);
  const [message, setMessage] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState<Row | null>(null);
  const [customers, setCustomers] = useState<Row[]>([]);

  useEffect(() => {
    if (portal !== "agency") return;
    apiGet<Row[]>("/api/v1/agency/customers")
      .then((data) => setCustomers(Array.isArray(data) ? data : []))
      .catch(() => setCustomers([]));
  }, [portal]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    const path =
      portal === "agency"
        ? `/api/v1/agency/agents/${selectedId}`
        : `/api/v1/customer/agents/${selectedId}`;
    apiGet<Row>(path)
      .then(setDetail)
      .catch((cause) => setMessage(isApiError(cause) ? cause.message : "Load agent failed."));
  }, [selectedId, portal, rows]);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend(listPath, "POST", {
        display_name: String(form.get("display_name") || ""),
        customer_id: String(form.get("customer_id") || "") || undefined,
      });
      setMessage("Agent draft created.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
    }
  }

  async function onConfigure(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId) return;
    const form = new FormData(event.currentTarget);
    const path =
      portal === "agency"
        ? `/api/v1/agency/agents/${selectedId}`
        : `/api/v1/customer/agents/${selectedId}`;
    try {
      await apiSend(path, "PATCH", {
        greeting: String(form.get("greeting") || ""),
        instructions: String(form.get("instructions") || ""),
        voice_provider: String(form.get("voice_provider") || ""),
        voice_id: String(form.get("voice_id") || ""),
        language: String(form.get("language") || "en"),
        timezone: String(form.get("timezone") || "UTC"),
        inbound_enabled: form.get("inbound_enabled") === "on",
        fallback_behavior: String(form.get("fallback_behavior") || "hangup"),
        voicemail_greeting: String(form.get("voicemail_greeting") || ""),
        default_transfer_id: String(form.get("default_transfer_id") || "") || null,
        business_hours: [
          {
            days: [1, 2, 3, 4, 5],
            start: String(form.get("hours_start") || "09:00"),
            end: String(form.get("hours_end") || "17:00"),
          },
        ],
      });
      setMessage("Agent configuration saved.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Save failed.");
    }
  }

  async function publish() {
    if (!selectedId || portal !== "agency") return;
    try {
      await apiSend(`/api/v1/agency/agents/${selectedId}/publish`, "POST", {});
      setMessage("Agent published.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Publish failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2>Agents</h2>
      </div>
      <Message value={error || message} />
      {portal === "agency" || portal === "customer" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>New agent</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void onCreate(e)}>
            {portal === "agency" ? (
              <label>
                Customer
                <select name="customer_id" required defaultValue="">
                  <option value="" disabled>
                    Select customer
                  </option>
                  {customers.map((c) => (
                    <option key={String(c.id)} value={String(c.id)}>
                      {cell(c.display_name)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <label>
              Name
              <input name="display_name" required />
            </label>
            <button type="submit">Create draft</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "display_name", label: "Name" },
          { key: "status", label: "Status" },
          { key: "customer_id", label: "Customer" },
          { key: "published_version", label: "Published" },
          { key: "production_routable", label: "Routable" },
          { key: "id", label: "Id" },
        ]}
        empty="No agents yet."
        onSelect={(row) => setSelectedId(String(row.id))}
      />
      {detail ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Builder — {cell(detail.display_name)}</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void onConfigure(e)}>
            <label className="col-span-full">
              Greeting
              <textarea name="greeting" rows={2} defaultValue={String(detail.greeting || "")} />
            </label>
            <label className="col-span-full">
              Instructions
              <textarea
                name="instructions"
                rows={4}
                defaultValue={String(detail.instructions || "")}
              />
            </label>
            <label>
              Voice provider
              <input name="voice_provider" defaultValue={String(detail.voice_provider || "")} />
            </label>
            <label>
              Voice id
              <input name="voice_id" defaultValue={String(detail.voice_id || "")} />
            </label>
            <label>
              Language
              <input name="language" defaultValue={String(detail.language || "en")} />
            </label>
            <label>
              Timezone
              <input name="timezone" defaultValue={String(detail.timezone || "UTC")} />
            </label>
            <label>
              Hours start
              <input name="hours_start" defaultValue="09:00" />
            </label>
            <label>
              Hours end
              <input name="hours_end" defaultValue="17:00" />
            </label>
            <label>
              After-hours / voicemail greeting
              <input
                name="voicemail_greeting"
                defaultValue={String(detail.voicemail_greeting || "")}
              />
            </label>
            <label>
              Default transfer id
              <input
                name="default_transfer_id"
                defaultValue={String(detail.default_transfer_id || "")}
              />
            </label>
            <label>
              Fallback
              <select
                name="fallback_behavior"
                defaultValue={String(detail.fallback_behavior || "hangup")}
              >
                <option value="hangup">Hang up</option>
                <option value="voicemail">Voicemail</option>
                <option value="transfer">Transfer</option>
              </select>
            </label>
            <label className="flex items-center gap-2 font-semibold">
              <input
                name="inbound_enabled"
                type="checkbox"
                defaultChecked={Boolean(detail.inbound_enabled)}
              />
              Inbound enabled
            </label>
            <div className="col-span-full flex flex-wrap gap-2">
              <button type="submit">Save draft</button>
              {portal === "agency" ? (
                <button type="button" className="bg-success text-text-inverse" onClick={() => void publish()}>
                  Publish
                </button>
              ) : null}
            </div>
          </form>
        </article>
      ) : null}
    </section>
  );
}

export function NumbersScreen({ portal }: { portal: Portal }) {
  const listPath =
    portal === "platform"
      ? "/api/v1/platform/phone-numbers"
      : "/api/v1/agency/phone-numbers";
  const { rows, error, refresh } = useRows(listPath);
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState<Row[]>([]);
  const [agents, setAgents] = useState<Row[]>([]);

  useEffect(() => {
    if (portal !== "agency") return;
    apiGet<Row[]>("/api/v1/agency/agents")
      .then((data) => setAgents(Array.isArray(data) ? data : []))
      .catch(() => setAgents([]));
  }, [portal]);

  async function stock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/api/v1/platform/phone-numbers", "POST", {
        e164: String(form.get("e164") || ""),
        country: String(form.get("country") || "US"),
        area: String(form.get("area") || ""),
        monthly_cost_minor: Number(form.get("monthly_cost_minor") || 0),
        provider: "platform",
        provider_ref: String(form.get("provider_ref") || "lab-stock"),
      });
      setMessage("Number stocked.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Stock failed.");
    }
  }

  async function doSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const qs = new URLSearchParams({
      country: String(form.get("country") || "US"),
      area: String(form.get("area") || ""),
    });
    try {
      const data = await apiGet<Row>(`/api/v1/agency/phone-numbers/search?${qs}`);
      setSearch(asList(data.inventory ?? data));
      setMessage("Search complete.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Search failed.");
    }
  }

  async function reserveAndAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const reserved = await apiSend<Row>("/api/v1/agency/phone-numbers/reservations", "POST", {
        number_id: String(form.get("number_id") || ""),
        agent_id: String(form.get("agent_id") || ""),
      });
      await apiSend("/api/v1/agency/phone-numbers/assignments", "POST", {
        reservation_id: reserved.id,
        confirm: true,
      });
      setMessage("Number assigned to agent.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Assign failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2>Phone numbers</h2>
      </div>
      <Message value={error || message} />
      {portal === "platform" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Stock lab inventory</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void stock(e)}>
            <label>
              E.164
              <input name="e164" placeholder="+15551234567" required />
            </label>
            <label>
              Country
              <input name="country" defaultValue="US" />
            </label>
            <label>
              Area
              <input name="area" defaultValue="555" />
            </label>
            <label>
              Monthly cost (minor)
              <input name="monthly_cost_minor" type="number" defaultValue={0} />
            </label>
            <button type="submit">Stock number</button>
          </form>
        </article>
      ) : null}
      {portal === "agency" ? (
        <>
          <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
            <h3>Search inventory</h3>
            <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void doSearch(e)}>
              <label>
                Country
                <input name="country" defaultValue="US" />
              </label>
              <label>
                Area
                <input name="area" />
              </label>
              <button type="submit">Search</button>
            </form>
            <DataTable
              rows={search}
              columns={[
                { key: "e164", label: "Number" },
                { key: "status", label: "Status" },
                { key: "id", label: "Id" },
              ]}
              empty="Run a search to list stock."
            />
          </article>
          <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
            <h3>Reserve & assign</h3>
            <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void reserveAndAssign(e)}>
              <label>
                Number id
                <input name="number_id" required />
              </label>
              <label>
                Agent
                <select name="agent_id" required defaultValue="">
                  <option value="" disabled>
                    Select agent
                  </option>
                  {agents.map((a) => (
                    <option key={String(a.id)} value={String(a.id)}>
                      {cell(a.display_name)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Customer id (optional)
                <input name="customer_id" />
              </label>
              <button type="submit">Assign</button>
            </form>
          </article>
        </>
      ) : null}
      <DataTable
        rows={
          portal === "agency"
            ? asList((rows as unknown as Row).assigned ? rows : rows)
            : rows
        }
        columns={[
          { key: "e164", label: "Number" },
          { key: "status", label: "Status" },
          { key: "assigned_agent_id", label: "Agent" },
          { key: "id", label: "Id" },
        ]}
        empty="No numbers yet."
      />
    </section>
  );
}

export function CallsScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform"
      ? "/api/v1/platform/calls"
      : portal === "agency"
        ? "/api/v1/agency/calls"
        : "/api/v1/customer/calls";
  const { rows, error, refresh } = useRows(path);
  const [selected, setSelected] = useState<Row | null>(null);
  const [message, setMessage] = useState("");
  const [recordingUrl, setRecordingUrl] = useState("");

  async function playRecording() {
    if (!selected?.id) return;
    try {
      const artifacts = await apiGet<Row[]>(
        `/api/v1/${portal}/calls/${selected.id}/artifacts`,
      );
      const list = Array.isArray(artifacts) ? artifacts : [];
      const first = list[0];
      if (!first?.id) {
        setMessage("No recording artifacts for this call yet.");
        setRecordingUrl("");
        return;
      }
      const grant = await apiSend<Row>(
        `/api/v1/${portal}/calls/${selected.id}/artifacts/${first.id}/access`,
        "POST",
        {},
      );
      setRecordingUrl(String(grant.url || grant.access_url || grant.signed_url || ""));
      setMessage("Short-lived recording grant issued.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Recording access failed.");
      setRecordingUrl("");
    }
  }

  async function originate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (portal !== "agency") return;
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/api/v1/agency/calls/outbound", "POST", {
        agent_id: String(form.get("agent_id") || ""),
        to: String(form.get("to") || ""),
      });
      setMessage("Outbound originate requested.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Originate failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2>Calls</h2>
      </div>
      <Message value={error || message} />
      {portal === "agency" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Outbound (lab)</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void originate(e)}>
            <label>
              Agent id
              <input name="agent_id" required />
            </label>
            <label>
              To E.164
              <input name="to" placeholder="+1555…" required />
            </label>
            <button type="submit">Originate</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "remote_e164", label: "Caller / remote" },
          { key: "e164", label: "DID" },
          { key: "direction", label: "Direction" },
          { key: "status", label: "Status" },
          { key: "duration_seconds", label: "Duration" },
          { key: "voicemail_status", label: "Voicemail" },
          { key: "id", label: "Id" },
        ]}
        empty="No calls yet — place a lab inbound after Wave 1C wiring."
        onSelect={setSelected}
      />
      {selected ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Call detail</h3>
          <dl className="grid gap-2">
            {Object.entries(selected).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{cell(value)}</dd>
              </div>
            ))}
          </dl>
          <p className="text-text-secondary">
            Transcripts are not stored as an application DB log column; recording play uses a
            short-lived grant to the recording plane.
          </p>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => void playRecording()}>
              Request recording play
            </button>
          </div>
          {recordingUrl ? (
            <audio controls src={recordingUrl}>
              <track kind="captions" />
            </audio>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}

export function BillingPlansScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform" ? "/api/v1/platform/plans" : "/api/v1/agency/plans";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (portal !== "platform") return;
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/api/v1/platform/plans", "POST", {
        name: String(form.get("name") || ""),
        price_minor: Number(form.get("amount_minor") || 0),
        included_minutes: Number(form.get("included_minutes") || 100),
        allow_topups: false,
        topup_minutes: 0,
        topup_price_minor: 0,
        overage_enabled: false,
        overage_price_per_minute_minor: 0,
        grace_seconds: 0,
      });
      setMessage("Plan created.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>Plans</h2>
      <Message value={error || message} />
      {portal === "platform" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Create plan</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void createPlan(e)}>
            <label>
              Name
              <input name="name" required />
            </label>
            <label>
              Amount (minor units)
              <input name="amount_minor" type="number" required />
            </label>
            <label>
              Interval
              <select name="interval" defaultValue="month">
                <option value="month">Month</option>
                <option value="year">Year</option>
              </select>
            </label>
            <button type="submit">Create</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "name", label: "Name" },
          { key: "amount_minor", label: "Amount" },
          { key: "interval", label: "Interval" },
          { key: "id", label: "Id" },
        ]}
        empty="No plans."
      />
    </section>
  );
}

export function PaymentsScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform"
      ? "/api/v1/platform/payments"
      : portal === "agency"
        ? "/api/v1/agency/wallet"
        : "/api/v1/customer/invoices";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function sandboxSettle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/webhooks/stripe/v1/", "POST", {
        id: String(form.get("event_id") || `evt_lab_${Date.now()}`),
        type: "checkout.session.completed",
        data: {
          object: {
            id: String(form.get("session_id") || `cs_lab_${Date.now()}`),
            payment_status: "paid",
            amount_total: Number(form.get("amount_minor") || 0),
            currency: "usd",
            client_reference_id: String(form.get("client_reference") || ""),
            metadata: { vokit_sandbox: "1" },
          },
        },
      });
      setMessage("Sandbox webhook posted (signature may be required in stricter modes).");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Sandbox settle failed.");
    }
  }

  async function topUp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (portal !== "agency") return;
    try {
      await apiSend("/api/v1/agency/payouts", "POST", {});
      setMessage("Payout requested for available wallet balance.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Payout request failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>{portal === "agency" ? "Wallet" : "Payments"}</h2>
      <Message value={error || message} />
      {portal === "platform" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Sandbox settle</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void sandboxSettle(e)}>
            <label>
              Client reference
              <input name="client_reference" required />
            </label>
            <label>
              Amount minor
              <input name="amount_minor" type="number" required />
            </label>
            <label>
              Event id
              <input name="event_id" />
            </label>
            <button type="submit">Post sandbox webhook</button>
          </form>
        </article>
      ) : null}
      {portal === "agency" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Request payout</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void topUp(e)}>
            <button type="submit">Request available balance</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "id", label: "Id" },
          { key: "status", label: "Status" },
          { key: "amount_minor", label: "Amount" },
          { key: "balance_minor", label: "Balance" },
        ]}
        empty="No payment rows."
      />
    </section>
  );
}

export function KnowledgeScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform"
      ? "/api/v1/platform/knowledge"
      : portal === "agency"
        ? "/api/v1/agency/knowledge"
        : "/api/v1/customer/knowledge";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function ingest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (portal === "platform") return;
    const form = new FormData(event.currentTarget);
    try {
      await apiSend(
        portal === "agency" ? "/api/v1/agency/knowledge" : "/api/v1/customer/knowledge",
        "POST",
        {
          agent_id: String(form.get("agent_id") || ""),
          title: String(form.get("title") || ""),
          body: String(form.get("body") || ""),
        },
      );
      setMessage("Knowledge ingested (memory/Qdrant per server config).");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Ingest failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>Knowledge</h2>
      <Message value={error || message} />
      {portal !== "platform" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Add FAQ / document</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void ingest(e)}>
            <label>
              Agent id
              <input name="agent_id" required />
            </label>
            <label>
              Title
              <input name="title" required />
            </label>
            <label className="col-span-full">
              Body
              <textarea name="body" rows={4} required />
            </label>
            <button type="submit">Ingest</button>
          </form>
          <p className="text-text-secondary">
            Optional Qdrant + FastEmbed: set QDRANT_URL and align Pipecat embeddings
            (see packages/pipecat-voice).
          </p>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "title", label: "Title" },
          { key: "agent_id", label: "Agent" },
          { key: "id", label: "Id" },
        ]}
        empty="No knowledge documents."
      />
    </section>
  );
}

export function KycRiskScreen({
  portal,
  kind,
}: {
  portal: Portal;
  kind: "kyc" | "risk";
}) {
  const path =
    kind === "kyc"
      ? portal === "platform"
        ? "/api/v1/platform/kyc/cases"
        : "/api/v1/agency/kyc"
      : portal === "platform"
        ? "/api/v1/platform/risk/cases"
        : "/api/v1/customer/risk";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function startKyc(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (portal !== "agency") return;
    try {
      await apiSend("/api/v1/agency/kyc/sessions", "POST", {});
      setMessage("External KYC session created (no document vault in-app — Q-015).");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "KYC start failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>{kind === "kyc" ? "KYC" : "Risk"}</h2>
      <Message value={error || message} />
      {kind === "kyc" && portal === "agency" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Start hosted KYC</h3>
          <p className="text-text-secondary">Documents stay with the external provider.</p>
          <form onSubmit={(e) => void startKyc(e)}>
            <button type="submit">Create session</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "status", label: "Status" },
          { key: "id", label: "Id" },
          { key: "agency_id", label: "Agency" },
        ]}
        empty={`No ${kind} cases.`}
      />
    </section>
  );
}

export function IntegrationsScreen({ portal }: { portal: Portal }) {
  const [customerId, setCustomerId] = useState("");
  const path =
    portal === "platform"
      ? "/api/v1/platform/integrations"
      : portal === "agency"
        ? customerId
          ? `/api/v1/agency/integrations?customer_id=${encodeURIComponent(customerId)}`
          : null
        : "/api/v1/customer/integrations";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const body = {
      provider: String(form.get("provider") || ""),
      display_name: String(form.get("display_name") || ""),
      customer_id: String(form.get("customer_id") || customerId || "") || undefined,
      secret: String(form.get("secret") || "lab-secret"),
    };
    try {
      await apiSend(
        portal === "agency" ? "/api/v1/agency/integrations" : "/api/v1/customer/integrations",
        "POST",
        body,
      );
      setMessage("Connection saved (memory adapter until HTTP providers are wired).");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Connect failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>Integrations</h2>
      <Message value={error || message} />
      {portal === "agency" ? (
        <label>
          Customer id
          <input value={customerId} onChange={(e) => setCustomerId(e.target.value)} required />
        </label>
      ) : null}
      {portal !== "platform" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Connect</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void connect(e)}>
            {portal === "agency" ? (
              <label>
                Customer id
                <input name="customer_id" defaultValue={customerId} required />
              </label>
            ) : null}
            <label>
              Provider
              <input name="provider" defaultValue="http_webhook" required />
            </label>
            <label>
              Display name
              <input name="display_name" required />
            </label>
            <label>
              Secret
              <input name="secret" type="password" />
            </label>
            <button type="submit">Save connection</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "display_name", label: "Name" },
          { key: "provider", label: "Provider" },
          { key: "status", label: "Status" },
          { key: "id", label: "Id" },
        ]}
        empty="No integrations."
      />
    </section>
  );
}

export function AuditScreen() {
  const { rows, error } = useRows("/api/v1/platform/audit-events");
  const [q, setQ] = useState("");
  const filtered = q
    ? rows.filter((row) => JSON.stringify(row).toLowerCase().includes(q.toLowerCase()))
    : rows;
  return (
    <section className="grid gap-4">
      <h2>Audit</h2>
      <Message value={error} />
      <label>
        Search
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter events" />
      </label>
      <DataTable
        rows={filtered}
        columns={[
          { key: "event_name", label: "Event" },
          { key: "actor_email", label: "Actor" },
          { key: "created_at", label: "When" },
          { key: "id", label: "Id" },
        ]}
        empty="No audit events."
      />
    </section>
  );
}

export function GenericModuleScreen({
  title,
  path,
}: {
  title: string;
  path: string;
}) {
  const { rows, error } = useRows(path);
  const columns =
    rows[0] != null
      ? Object.keys(rows[0])
          .slice(0, 6)
          .map((key) => ({ key, label: key }))
      : [{ key: "id", label: "Id" }];
  return (
    <section className="grid gap-4">
      <h2>{title}</h2>
      <Message value={error} />
      <DataTable rows={rows} columns={columns} empty={`No ${title.toLowerCase()} yet.`} />
    </section>
  );
}

export function TransfersScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform" ? "/api/v1/platform/transfers" : "/api/v1/agency/transfers";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (portal !== "agency") return;
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/api/v1/agency/transfers", "POST", {
        display_name: String(form.get("display_name") || ""),
        e164: String(form.get("e164") || ""),
        customer_id: String(form.get("customer_id") || "") || undefined,
      });
      setMessage("Transfer destination created.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>Transfer destinations</h2>
      <Message value={error || message} />
      {portal === "agency" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Add destination</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void onCreate(e)}>
            <label>
              Name
              <input name="display_name" required />
            </label>
            <label>
              E.164
              <input name="e164" placeholder="+15550001002" required />
            </label>
            <label>
              Customer id
              <input name="customer_id" />
            </label>
            <button type="submit">Create</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "display_name", label: "Name" },
          { key: "e164", label: "Number" },
          { key: "status", label: "Status" },
          { key: "id", label: "Id" },
        ]}
        empty="No transfer destinations."
      />
    </section>
  );
}

export function TeamScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform"
      ? "/api/v1/platform/users"
      : portal === "agency"
        ? "/api/v1/agency/team"
        : "/api/v1/customer/team";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend(path, "POST", {
        email: String(form.get("email") || ""),
        role: String(form.get("role") || ""),
      });
      setMessage("Invitation sent.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Invite failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>{portal === "platform" ? "Users" : "Team"}</h2>
      <Message value={error || message} />
      <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
        <h3>Invite</h3>
        <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void invite(e)}>
          <label>
            Email
            <input name="email" type="email" required />
          </label>
          <label>
            Role
            <input
              name="role"
              placeholder={
                portal === "platform"
                  ? "finance_admin"
                  : portal === "agency"
                    ? "agency_admin"
                    : "customer_admin"
              }
              required
            />
          </label>
          <button type="submit">Invite</button>
        </form>
      </article>
      <DataTable
        rows={rows}
        columns={[
          { key: "email", label: "Email" },
          { key: "role", label: "Role" },
          { key: "status", label: "Status" },
          { key: "id", label: "Id" },
        ]}
        empty="No team members."
      />
    </section>
  );
}

export function WebhooksScreen() {
  const { rows, error, refresh } = useRows("/api/v1/agency/webhooks");
  const [message, setMessage] = useState("");

  async function createEndpoint(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/api/v1/agency/webhooks", "POST", {
        url: String(form.get("url") || ""),
        customer_id: String(form.get("customer_id") || ""),
      });
      setMessage("Webhook endpoint created (tenant signing secret server-side).");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>Webhooks</h2>
      <Message value={error || message} />
      <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
        <h3>Add endpoint</h3>
        <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void createEndpoint(e)}>
          <label>
            Customer id
            <input name="customer_id" required />
          </label>
          <label className="col-span-full">
            URL
            <input name="url" type="url" required />
          </label>
          <button type="submit">Create</button>
        </form>
      </article>
      <DataTable
        rows={rows}
        columns={[
          { key: "url", label: "URL" },
          { key: "status", label: "Status" },
          { key: "id", label: "Id" },
        ]}
        empty="No webhook endpoints."
      />
    </section>
  );
}

export function SettingsScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform"
      ? "/api/v1/platform/settings"
      : "/api/v1/agency/notification-preferences";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function patch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (portal !== "platform") return;
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/api/v1/platform/settings", "PATCH", {
        support_email: String(form.get("support_email") || ""),
      });
      setMessage("Settings updated.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Update failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>Settings</h2>
      <Message value={error || message} />
      {portal === "platform" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <h3>Platform settings</h3>
          <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(e) => void patch(e)}>
            <label>
              Support email
              <input name="support_email" type="email" />
            </label>
            <button type="submit">Save</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={
          rows[0]
            ? Object.keys(rows[0])
                .slice(0, 6)
                .map((key) => ({ key, label: key }))
            : [{ key: "id", label: "Id" }]
        }
        empty="No settings rows."
      />
    </section>
  );
}

export function InvoicesScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform"
      ? "/api/v1/platform/invoices"
      : portal === "agency"
        ? "/api/v1/agency/customer-invoices"
        : "/api/v1/customer/invoices";
  return <GenericModuleScreen title="Invoices" path={path} />;
}

export function PayoutsScreen({ portal }: { portal: Portal }) {
  const path =
    portal === "platform" ? "/api/v1/platform/payouts" : "/api/v1/agency/payouts";
  const { rows, error, refresh } = useRows(path);
  const [message, setMessage] = useState("");

  async function requestPayout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (portal !== "agency") return;
    try {
      await apiSend("/api/v1/agency/payouts", "POST", {});
      setMessage("Payout requested.");
      refresh();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Request failed.");
    }
  }

  return (
    <section className="grid gap-4">
      <h2>Payouts</h2>
      <Message value={error || message} />
      {portal === "agency" ? (
        <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
          <form onSubmit={(e) => void requestPayout(e)}>
            <button type="submit">Request available balance</button>
          </form>
        </article>
      ) : null}
      <DataTable
        rows={rows}
        columns={[
          { key: "status", label: "Status" },
          { key: "amount_minor", label: "Amount" },
          { key: "id", label: "Id" },
        ]}
        empty="No payouts."
      />
    </section>
  );
}

export function renderLegacyProductScreen(
  portal: Portal,
  route: string,
  fallbackPath: string,
  fallbackTitle: string,
) {
  switch (route) {
    case "agencies":
      return <AgenciesScreen />;
    case "customers":
      return <CustomersScreen portal={portal} />;
    case "agents":
      return <AgentsScreen portal={portal} />;
    case "numbers":
      return <NumbersScreen portal={portal} />;
    case "calls":
      return <CallsScreen portal={portal} />;
    case "plans":
      return <BillingPlansScreen portal={portal} />;
    case "payments":
    case "wallet":
      return <PaymentsScreen portal={portal} />;
    case "payouts":
      return <PayoutsScreen portal={portal} />;
    case "invoices":
      return <InvoicesScreen portal={portal} />;
    case "knowledge":
      return <KnowledgeScreen portal={portal} />;
    case "kyc":
      return <KycRiskScreen portal={portal} kind="kyc" />;
    case "risk":
      return <KycRiskScreen portal={portal} kind="risk" />;
    case "disputes":
      return <GenericModuleScreen title="Disputes" path="/api/v1/platform/disputes" />;
    case "integrations":
      return <IntegrationsScreen portal={portal} />;
    case "webhooks":
      return <WebhooksScreen />;
    case "transfers":
      return <TransfersScreen portal={portal} />;
    case "team":
    case "users":
      return <TeamScreen portal={portal} />;
    case "settings":
    case "preferences":
      return <SettingsScreen portal={portal} />;
    case "audit":
      return <AuditScreen />;
    default:
      return <GenericModuleScreen title={fallbackTitle} path={fallbackPath} />;
  }
}