import { FormEvent, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import {
  PLATFORM_MODULES,
  cellValue,
  type PlatformModuleConfig,
} from "./platformModules";

function ApiGapNote({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-lg border border-dashed border-border-strong bg-canvas px-3 py-2 text-body-sm text-text-muted">
      {children}
    </p>
  );
}

function asRows(data: unknown, objectMode?: boolean): Record<string, unknown>[] {
  if (objectMode) {
    if (data && typeof data === "object" && !Array.isArray(data)) {
      return [data as Record<string, unknown>];
    }
    return [];
  }
  if (Array.isArray(data)) {
    return data as Record<string, unknown>[];
  }
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of ["results", "items", "cases", "events"]) {
      if (Array.isArray(record[key])) {
        return record[key] as Record<string, unknown>[];
      }
    }
  }
  return [];
}

function statusTone(value: unknown): BadgeTone {
  const status = String(value ?? "").toLowerCase();
  if (["active", "paid", "settled", "ready", "verified", "healthy"].includes(status)) {
    return "success";
  }
  if (["pending", "requested", "open", "draft", "processing", "under_review"].includes(status)) {
    return "warning";
  }
  if (["failed", "suspended", "rejected", "error", "chargeback", "banned"].includes(status)) {
    return "danger";
  }
  if (["info", "completed", "ended"].includes(status)) {
    return "info";
  }
  return "neutral";
}

function usePlatformModule(config: PlatformModuleConfig) {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGet<unknown>(config.path);
      setRows(asRows(data, config.objectMode));
      setError("");
    } catch (cause) {
      setRows([]);
      setError(isApiError(cause) ? cause.message : `Failed to load ${config.title}.`);
    } finally {
      setLoading(false);
    }
  }, [config.path, config.objectMode, config.title]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((row) =>
      Object.values(row)
        .map((value) => cellValue(value).toLowerCase())
        .join(" ")
        .includes(q),
    );
  }, [rows, query]);

  return { rows: filtered, error, message, setMessage, loading, query, setQuery, reload };
}

export function PlatformResourceScreen({ route }: { route: string }) {
  const config = PLATFORM_MODULES[route];
  if (!config) {
    return (
      <section className="mx-auto max-w-[1200px]">
        <h1 className="m-0 text-[1.85rem] font-bold text-text-primary">Module not configured</h1>
        <p className="mt-2 text-body text-text-muted">Route: {route}</p>
      </section>
    );
  }

  if (route === "instructions") {
    return <PlatformInstructionsScreen config={config} />;
  }
  if (route === "settings") {
    return <PlatformSettingsScreen config={config} />;
  }

  return <PlatformListScreen config={config} />;
}

function PlatformListScreen({ config }: { config: PlatformModuleConfig }) {
  const { rows, error, loading, query, setQuery, reload } = usePlatformModule(config);

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            {config.title}
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            {config.subtitle}
            {config.permissionHint ? ` · ${config.permissionHint}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="m-0 font-normal">
            <span className="sr-only">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search…"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
        </div>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}

      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="m-0 py-10 text-center text-body text-text-muted">{config.empty}</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  {config.columns.map((col) => (
                    <th key={col.key} className="border-0 px-2 py-2 text-left">
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={String(row.id ?? index)}>
                    {config.columns.map((col) => (
                      <td key={col.key} className="px-2 py-3 text-text-secondary">
                        {col.key === "status" || col.key === "agency_status" ? (
                          <StatusBadge tone={statusTone(row[col.key])}>
                            {cellValue(row[col.key])}
                          </StatusBadge>
                        ) : (
                          <span
                            className={
                              col.key === "display_name" || col.key === "name" || col.key === "title"
                                ? "font-semibold text-text-primary"
                                : undefined
                            }
                          >
                            {cellValue(row[col.key])}
                          </span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      {(config.apiGaps ?? []).map((gap) => (
        <div key={gap} className="mt-3">
          <ApiGapNote>{gap}</ApiGapNote>
        </div>
      ))}
    </section>
  );
}

function PlatformInstructionsScreen({ config }: { config: PlatformModuleConfig }) {
  const { rows, error, message, setMessage, loading, reload } = usePlatformModule(config);
  const body = String(rows[0]?.body ?? "");

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend(config.path, "POST", { body: String(form.get("body") || "") });
      setMessage("Platform instructions saved.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Save failed.");
    }
  }

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6">
        <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
          {config.title}
        </h1>
        <p className="mt-1 mb-0 text-body text-text-muted">{config.subtitle}</p>
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
      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading…</p>
        ) : (
          <form className="grid gap-3" onSubmit={(event) => void onSave(event)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Instruction body</span>
              <textarea
                name="body"
                rows={12}
                defaultValue={body}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <div>
              <ActionButton type="submit">Save instructions</ActionButton>
            </div>
          </form>
        )}
      </article>
    </section>
  );
}

function PlatformSettingsScreen({ config }: { config: PlatformModuleConfig }) {
  const { rows, error, message, setMessage, loading, reload } = usePlatformModule(config);
  const settings = rows[0] ?? {};

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiSend(config.path, "PATCH", {
        support_email: String(form.get("support_email") || ""),
      });
      setMessage("Settings updated.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Update failed.");
    }
  }

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6">
        <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
          {config.title}
        </h1>
        <p className="mt-1 mb-0 text-body text-text-muted">{config.subtitle}</p>
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
      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading…</p>
        ) : (
          <form className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end" onSubmit={(e) => void onSave(e)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Support email</span>
              <input
                name="support_email"
                type="email"
                defaultValue={String(settings.support_email ?? "")}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit">Save</ActionButton>
          </form>
        )}
      </article>
      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <h2 className="m-0 mb-3 text-section text-text-primary">Current settings payload</h2>
        <pre className="m-0 overflow-auto rounded-xl bg-canvas p-4 text-body-sm text-text-secondary">
          {JSON.stringify(settings, null, 2)}
        </pre>
      </article>
    </section>
  );
}
