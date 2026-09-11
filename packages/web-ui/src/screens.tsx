import { FormEvent, useEffect, useState } from "react";

import {
  DashboardPayload,
  Portal,
  apiGet,
  apiSend,
  getDashboard,
  isApiError,
} from "@/api";

function asRows(data: unknown): Record<string, unknown>[] {
  if (Array.isArray(data)) {
    return data as Record<string, unknown>[];
  }
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    if (Array.isArray(record.settings)) {
      return record.settings as Record<string, unknown>[];
    }
    if (Array.isArray(record.lots)) {
      return record.lots as Record<string, unknown>[];
    }
    return [record];
  }
  return [];
}

function cell(value: unknown): string {
  if (value == null) {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

export function DashboardScreen({
  portal,
  onNavigate,
}: {
  portal: Portal;
  onNavigate: (href: string) => void;
}) {
  const [period, setPeriod] = useState("30d");
  const [timezone, setTimezone] = useState("UTC");
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");
  const [agencyId, setAgencyId] = useState("");
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (period === "custom" && (!since || !until)) {
      return;
    }
    let active = true;
    getDashboard(portal, {
      period,
      timezone,
      since: period === "custom" ? since : undefined,
      until: period === "custom" ? until : undefined,
      agencyId: portal === "platform" ? agencyId : undefined,
    })
      .then((payload) => {
        if (active) {
          setData(payload);
          setError("");
        }
      })
      .catch((cause) => {
        if (active) {
          setError(isApiError(cause) ? cause.message : "Dashboard failed.");
        }
      });
    return () => {
      active = false;
    };
  }, [portal, period, timezone, since, until, agencyId]);

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2>Dashboard</h2>
        <label className="flex flex-wrap items-center gap-3 font-semibold" htmlFor="period">
          Period
          <select
            id="period"
            value={period}
            onChange={(event) => setPeriod(event.target.value)}
          >
            <option value="today">Today</option>
            <option value="7d">7 days</option>
            <option value="30d">30 days</option>
            <option value="mtd">Month to date</option>
            <option value="custom">Custom</option>
          </select>
        </label>
        <label className="flex flex-wrap items-center gap-3 font-semibold" htmlFor="timezone">
          Timezone
          <select
            id="timezone"
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
          >
            <option value="UTC">UTC</option>
            <option value="America/New_York">America/New_York</option>
            <option value="Europe/London">Europe/London</option>
            <option value="Asia/Karachi">Asia/Karachi</option>
          </select>
        </label>
        {period === "custom" ? (
          <>
            <label className="flex flex-wrap items-center gap-3 font-semibold" htmlFor="since">
              Since
              <input
                id="since"
                type="datetime-local"
                value={since}
                onChange={(event) => setSince(event.target.value)}
              />
            </label>
            <label className="flex flex-wrap items-center gap-3 font-semibold" htmlFor="until">
              Until
              <input
                id="until"
                type="datetime-local"
                value={until}
                onChange={(event) => setUntil(event.target.value)}
              />
            </label>
          </>
        ) : null}
        {portal === "platform" ? (
          <label className="flex flex-wrap items-center gap-3 font-semibold" htmlFor="agency-filter">
            Agency filter
            <input
              id="agency-filter"
              value={agencyId}
              onChange={(event) => setAgencyId(event.target.value)}
              placeholder="Optional agency_id"
            />
          </label>
        ) : null}
      </div>
      {error ? (
        <p className="text-danger" role="alert">
          {error}
        </p>
      ) : null}
      {data ? (
        <>
          <p className="text-text-secondary">
            Source {data.source}. Timezone {data.period.timezone}. Values come from
            ledger and control-plane projections, not the browser.
          </p>
          <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(160px,1fr))]">
            {data.kpis.map((card) => (
              <button
                key={card.key}
                type="button"
                className="grid cursor-pointer gap-2 rounded-lg border border-border-default bg-surface p-5 text-left"
                aria-label={`${card.label}: ${cell(card.value)}`}
                onClick={() => onNavigate(`#${card.href}`)}
              >
                <span className="text-sm text-text-secondary">{card.label}</span>
                <strong>{cell(card.value)}</strong>
              </button>
            ))}
          </div>
          {data.financial ? (
            <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
              <h3>Financial summary</h3>
              <dl className="grid gap-2">
                {Object.entries(data.financial).map(([key, value]) => (
                  <div key={key}>
                    <dt>{key}</dt>
                    <dd>{cell(value)}</dd>
                  </div>
                ))}
              </dl>
            </article>
          ) : null}
          {data.alerts ? (
            <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
              <h3>Alerts</h3>
              <dl className="grid gap-2">
                {Object.entries(data.alerts).map(([key, value]) => (
                  <div key={key}>
                    <dt>{key}</dt>
                    <dd>{cell(value)}</dd>
                  </div>
                ))}
              </dl>
            </article>
          ) : null}
          {typeof data.failed_calls === "number" ? (
            <p className="text-text-secondary">Failed calls in period: {data.failed_calls}</p>
          ) : null}
          {data.recent_calls && data.recent_calls.length > 0 ? (
            <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
              <h3>Recent calls</h3>
              <div className="overflow-auto rounded-lg border border-border-default bg-surface">
                <table>
                  <caption>Recent calls</caption>
                  <thead>
                    <tr>
                      <th>id</th>
                      <th>status</th>
                      <th>direction</th>
                      <th>minutes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_calls.map((row) => (
                      <tr key={String(row.id)}>
                        <td>{cell(row.id)}</td>
                        <td>{cell(row.status)}</td>
                        <td>{cell(row.direction)}</td>
                        <td>{cell(row.billed_minutes)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>
          ) : null}
        </>
      ) : (
        <p>Loading dashboard…</p>
      )}
    </section>
  );
}

export function ResourceScreen({
  title,
  path,
  portal,
  route,
}: {
  title: string;
  path: string;
  portal: Portal;
  route: string;
}) {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [reload, setReload] = useState(0);

  const listPath =
    portal === "agency" && route === "integrations" && customerId
      ? `${path}?customer_id=${encodeURIComponent(customerId)}`
      : path;

  useEffect(() => {
    if (portal === "agency" && route === "integrations" && !customerId) {
      setRows([]);
      return;
    }
    let active = true;
    apiGet<unknown>(listPath)
      .then((data) => {
        if (active) {
          setRows(asRows(data));
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
  }, [listPath, portal, route, customerId, reload]);

  const columns = rows[0] ? Object.keys(rows[0]).slice(0, 6) : [];

  return (
    <section className="grid gap-4">
      <h2>{title}</h2>
      {portal === "agency" && route === "integrations" ? (
        <label htmlFor="customer-id">
          Customer ID
          <input
            id="customer-id"
            value={customerId}
            onChange={(event) => setCustomerId(event.target.value)}
            placeholder="Required — connections are customer-owned"
          />
        </label>
      ) : null}
      {error ? (
        <p className="text-danger" role="alert">
          {error}
        </p>
      ) : null}
      <ActionForms portal={portal} route={route} onDone={() => setReload((n) => n + 1)} />
      <div className="overflow-auto rounded-lg border border-border-default bg-surface">
        <table>
          <caption>{title} records</caption>
          <thead>
            <tr>
              {columns.map((name) => (
                <th key={name} scope="col">
                  {name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={String(row.id ?? index)}>
                {columns.map((name) => (
                  <td key={name}>{cell(row[name])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 ? <p className="text-text-secondary">No rows in this scope.</p> : null}
      </div>
    </section>
  );
}

function ActionForms({
  portal,
  route,
  onDone,
}: {
  portal: Portal;
  route: string;
  onDone: () => void;
}) {
  const [message, setMessage] = useState("");

  async function submit(
    event: FormEvent<HTMLFormElement>,
    path: string,
    method: "POST" | "PUT" | "PATCH",
  ) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload: Record<string, unknown> = {};
    form.forEach((value, key) => {
      if (typeof value === "string" && value !== "") {
        if (key === "value" && /^-?\d+$/.test(value)) {
          payload[key] = Number(value);
        } else if (key.endsWith("_minor") || key.endsWith("_bps")) {
          payload[key] = Number(value);
        } else {
          payload[key] = value;
        }
      }
    });
    try {
      await apiSend(path, method, payload);
      setMessage("Saved.");
      onDone();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Action failed.");
    }
  }

  if (portal === "platform" && route === "agencies") {
    return (
      <article className="grid gap-3 rounded-lg border border-border-default bg-surface p-5">
        <h3>Create agency</h3>
        <p className="text-text-secondary">
          The browser never selects a tenant database. Host metadata is sent to the
          control-plane registry only.
        </p>
        <AgencyCreateForm
          onMessage={setMessage}
          onDone={onDone}
        />
        {message ? <p className="text-text-secondary">{message}</p> : null}
      </article>
    );
  }
  if (portal === "platform" && route === "customers") {
    return (
      <form
        className="grid items-end gap-3 rounded-lg border border-border-default bg-surface p-5 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]"
        onSubmit={(event) => void submit(event, "/api/v1/platform/customers", "POST")}
      >
        <h3>Create customer under agency</h3>
        <input name="display_name" placeholder="Customer name" required />
        <input name="agency_id" placeholder="Agency id" required />
        <button type="submit">Create</button>
        {message ? <p className="text-text-secondary">{message}</p> : null}
      </form>
    );
  }
  if (portal === "agency" && route === "customers") {
    return (
      <form
        className="grid items-end gap-3 rounded-lg border border-border-default bg-surface p-5 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]"
        onSubmit={(event) => void submit(event, "/api/v1/agency/customers", "POST")}
      >
        <h3>Create customer</h3>
        <input name="display_name" placeholder="Customer name" required />
        <button type="submit">Create</button>
        {message ? <p className="text-text-secondary">{message}</p> : null}
      </form>
    );
  }
  if (portal === "agency" && route === "payouts") {
    return (
      <form className="grid items-end gap-3 rounded-lg border border-border-default bg-surface p-5 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(event) => void submit(event, "/api/v1/agency/payouts", "POST")}>
        <h3>Request payout</h3>
        <button type="submit">Request available balance</button>
        {message ? <p className="text-text-secondary">{message}</p> : null}
      </form>
    );
  }
  if (portal === "customer" && route === "usage") {
    return (
      <form
        className="grid items-end gap-3 rounded-lg border border-border-default bg-surface p-5 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]"
        onSubmit={async (event) => {
          event.preventDefault();
          try {
            await apiSend(
              "/api/v1/customer/usage/top-ups",
              "POST",
              {},
              { "Idempotency-Key": crypto.randomUUID() },
            );
            setMessage("Top-up invoice created.");
            onDone();
          } catch (cause) {
            setMessage(isApiError(cause) ? cause.message : "Action failed.");
          }
        }}
      >
        <h3>Buy top-up</h3>
        <button type="submit">Purchase plan top-up</button>
        {message ? <p className="text-text-secondary">{message}</p> : null}
      </form>
    );
  }
  if (portal === "agency" && route === "kyc") {
    return (
      <form className="grid items-end gap-3 rounded-lg border border-border-default bg-surface p-5 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(event) => void submit(event, "/api/v1/agency/kyc/session", "POST")}>
        <h3>Start external KYC</h3>
        <button type="submit">Open hosted session</button>
        {message ? <p className="text-text-secondary">{message}</p> : null}
      </form>
    );
  }
  if (route === "notifications") {
    return (
      <NotificationActions
        portal={portal}
        onMessage={setMessage}
        message={message}
      />
    );
  }
  if (portal === "platform" && route === "settings") {
    return (
      <form
        className="grid items-end gap-3 rounded-lg border border-border-default bg-surface p-5 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]"
        onSubmit={(event) => void submit(event, "/api/v1/platform/settings", "PATCH")}
      >
        <h3>Update setting</h3>
        <input name="key" placeholder="payout.hold_days" required />
        <input name="value" placeholder="15" required />
        <input name="reason" placeholder="Reason" required />
        <button type="submit">Save</button>
        {message ? <p className="text-text-secondary">{message}</p> : null}
      </form>
    );
  }
  if (route === "team" || (portal === "platform" && route === "users")) {
    const path = portal === "platform" ? "/api/v1/platform/users" : `/api/v1/${portal}/team`;
    return (
      <form className="grid items-end gap-3 rounded-lg border border-border-default bg-surface p-5 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(event) => void submit(event, path, "POST")}>
        <h3>Invite</h3>
        <input name="email" type="email" placeholder="Email" required />
        <input name="role" placeholder={portal === "platform" ? "super_admin" : `${portal}_admin`} required />
        {portal === "platform" ? <input name="principal_type" placeholder="platform" required /> : null}
        <button type="submit">Invite</button>
        {message ? <p className="text-text-secondary">{message}</p> : null}
      </form>
    );
  }
  return null;
}

function AgencyCreateForm({
  onMessage,
  onDone,
}: {
  onMessage: (value: string) => void;
  onDone: () => void;
}) {
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend("/api/v1/platform/agencies", "POST", {
        display_name: String(form.get("display_name") || ""),
        legal_name: String(form.get("legal_name") || ""),
        owner_email: String(form.get("owner_email") || ""),
        commission_rate_bps: Number(form.get("commission_rate_bps") || 0),
      });
      onMessage("Agency created. Tenant database allocated on the server.");
      onDone();
    } catch (cause) {
      onMessage(isApiError(cause) ? cause.message : "Create failed.");
    }
  }
  return (
    <form className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]" onSubmit={(event) => void onSubmit(event)}>
      <input name="display_name" placeholder="Display name" required />
      <input name="legal_name" placeholder="Legal name" required />
      <input name="owner_email" type="email" placeholder="Owner email" required />
      <input
        name="commission_rate_bps"
        type="number"
        min={0}
        max={10000}
        defaultValue={1500}
        placeholder="Commission bps"
        required
      />
      <p className="text-text-secondary">
        MySQL database host, name, and credentials are allocated from server settings —
        never entered in the browser.
      </p>
      <button type="submit">Create agency</button>
    </form>
  );
}

function NotificationActions({
  portal,
  onMessage,
  message,
}: {
  portal: Portal;
  onMessage: (value: string) => void;
  message: string;
}) {
  const [notificationId, setNotificationId] = useState("");
  return (
    <form
      className="grid items-end gap-3 rounded-lg border border-border-default bg-surface p-5 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]"
      onSubmit={async (event) => {
        event.preventDefault();
        try {
          await apiSend(`/api/v1/${portal}/notifications/${notificationId}/read`, "POST", {});
          onMessage("Marked read.");
        } catch (cause) {
          onMessage(isApiError(cause) ? cause.message : "Update failed.");
        }
      }}
    >
      <h3>Mark notification read</h3>
      <input
        value={notificationId}
        onChange={(event) => setNotificationId(event.target.value)}
        placeholder="Notification id"
        required
      />
      <button type="submit">Mark read</button>
      {message ? <p className="text-text-secondary">{message}</p> : null}
    </form>
  );
}
