import { FormEvent, useState, type ReactNode } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { usePlatformTemplates } from "./hooks/usePlatformTemplates";
import {
  AGENT_TYPES,
  TEMPLATE_TOOLS,
  VISIBILITY_OPTIONS,
} from "./types";

type Tab = "metadata" | "visibility" | "install" | "versions";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "archived") return "danger";
  return "neutral";
}

function ApiNote({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-lg border border-dashed border-border-strong bg-canvas px-3 py-2 text-body-sm text-text-muted">
      {children}
    </p>
  );
}

export function PlatformTemplatesScreen() {
  const {
    templates,
    agencies,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    visibilityFilter,
    setVisibilityFilter,
    reload,
    createTemplate,
  } = usePlatformTemplates();

  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState<Tab>("metadata");
  const [tools, setTools] = useState<string[]>([]);
  const [selectedAgencies, setSelectedAgencies] = useState<string[]>([]);
  const [visibility, setVisibility] = useState("global");

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createTemplate({
        name: String(form.get("name") || ""),
        industry: String(form.get("industry") || ""),
        use_case: String(form.get("use_case") || ""),
        description: String(form.get("description") || ""),
        languages: String(form.get("languages") || "en"),
        visibility,
        selected_agency_ids: visibility === "selected" ? selectedAgencies : [],
        agent_type: String(form.get("agent_type") || "custom"),
        instructions: String(form.get("instructions") || ""),
        voice_provider: String(form.get("voice_provider") || ""),
        voice_id: String(form.get("voice_id") || ""),
        language: String(form.get("language") || "en"),
        tools,
        fallback_behavior: String(form.get("fallback_behavior") || "message"),
      });
      setShowCreate(false);
      event.currentTarget.reset();
      setTools([]);
      setSelectedAgencies([]);
      setVisibility("global");
      setTab("metadata");
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "metadata", label: "Metadata" },
    { id: "visibility", label: "Visibility" },
    { id: "versions", label: "Versions" },
    { id: "install", label: "Install / clone" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Templates
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA6-001–004 · Permission: agents.review
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Create template"}
          </ActionButton>
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
          <h2 className="m-0 text-section text-text-primary">Create template</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            Creates a reusable template and initial version (v1) with metadata, instructions,
            voice defaults, and tool allowlist.
          </p>
          <form className="grid gap-4" onSubmit={(event) => void onCreate(event)}>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <Field label="Name" name="name" required />
              <Field label="Industry" name="industry" />
              <Field label="Use case" name="use_case" />
              <Field label="Languages" name="languages" defaultValue="en" />
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Agent type</span>
                <select
                  name="agent_type"
                  defaultValue="custom"
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  {AGENT_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </label>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Visibility</span>
                <select
                  value={visibility}
                  onChange={(event) => setVisibility(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  {VISIBILITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <Field label="Voice provider" name="voice_provider" />
              <Field label="Voice id" name="voice_id" />
              <Field label="Default language" name="language" defaultValue="en" />
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Fallback</span>
                <select
                  name="fallback_behavior"
                  defaultValue="message"
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  <option value="message">message</option>
                  <option value="transfer">transfer</option>
                  <option value="hangup">hangup</option>
                </select>
              </label>
            </div>

            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Description</span>
              <textarea
                name="description"
                rows={2}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>

            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Template instructions</span>
              <textarea
                name="instructions"
                rows={5}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>

            {visibility === "selected" ? (
              <div>
                <p className="mb-2 mt-0 text-body-sm font-semibold text-text-primary">
                  Selected agencies
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {agencies.map((agency) => (
                    <label key={agency.id} className="m-0 flex items-center gap-2 font-normal">
                      <input
                        type="checkbox"
                        checked={selectedAgencies.includes(agency.id)}
                        onChange={(event) => {
                          setSelectedAgencies((prev) =>
                            event.target.checked
                              ? [...prev, agency.id]
                              : prev.filter((id) => id !== agency.id),
                          );
                        }}
                      />
                      <span className="text-body text-text-secondary">
                        {agency.display_name || agency.id.slice(0, 8)}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ) : null}

            <div>
              <p className="mb-2 mt-0 text-body-sm font-semibold text-text-primary">
                Recommended tools
              </p>
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                {TEMPLATE_TOOLS.map((tool) => (
                  <label key={tool} className="m-0 flex items-center gap-2 font-normal">
                    <input
                      type="checkbox"
                      checked={tools.includes(tool)}
                      onChange={(event) => {
                        setTools((prev) =>
                          event.target.checked
                            ? [...prev, tool]
                            : prev.filter((item) => item !== tool),
                        );
                      }}
                    />
                    <span className="text-body text-text-secondary">{tool}</span>
                  </label>
                ))}
              </div>
            </div>

            <ApiNote>
              Transfer rules metadata is not accepted by POST /api/v1/platform/templates yet.
              Use the transfer_call tool allowlist where needed.
            </ApiNote>

            <div>
              <ActionButton type="submit" disabled={busy}>
                Create template
              </ActionButton>
            </div>
          </form>
        </article>
      ) : null}

      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <div className="mb-4 grid gap-3 lg:grid-cols-2">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Name, industry, use case…"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Visibility</span>
            <select
              value={visibilityFilter}
              onChange={(event) => setVisibilityFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All</option>
              {VISIBILITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <h2 className="m-0 mb-3 text-section text-text-primary">
          Template catalog
          <span className="ml-2 text-body font-normal text-text-muted">({templates.length})</span>
        </h2>

        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading templates…</p>
        ) : templates.length === 0 ? (
          <p className="m-0 py-10 text-center text-body text-text-muted">No templates yet.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Name</th>
                  <th className="border-0 px-2 py-2 text-left">Industry</th>
                  <th className="border-0 px-2 py-2 text-left">Use case</th>
                  <th className="border-0 px-2 py-2 text-left">Visibility</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Version</th>
                </tr>
              </thead>
              <tbody>
                {templates.map((row) => (
                  <tr
                    key={row.id}
                    className={
                      selectedId === row.id
                        ? "cursor-pointer bg-brand-subtle/40"
                        : "cursor-pointer hover:bg-canvas"
                    }
                    onClick={() => {
                      setSelectedId(row.id);
                      setTab("metadata");
                    }}
                  >
                    <td className="px-2 py-3 font-semibold text-text-primary">
                      {row.name || row.id.slice(0, 8)}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.industry || "—"}</td>
                    <td className="px-2 py-3 text-text-secondary">{row.use_case || "—"}</td>
                    <td className="px-2 py-3 text-text-secondary">{row.visibility || "—"}</td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "unknown"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      {row.latest_version ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      {selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="m-0 text-section text-text-primary">
                {selected.name || selected.id.slice(0, 8)}
              </h2>
              <p className="mt-1 mb-0 text-body text-text-muted">
                {selected.industry || "—"} · {selected.use_case || "—"} · {selected.id}
              </p>
            </div>
            <StatusBadge tone={statusTone(selected.status)}>
              {selected.status || "unknown"}
            </StatusBadge>
          </div>

          <div className="mb-4 flex flex-wrap gap-2">
            {tabs.map((item) => (
              <button
                key={item.id}
                type="button"
                className={
                  tab === item.id
                    ? "rounded-xl bg-brand px-3.5 py-2 text-body font-semibold text-text-inverse"
                    : "rounded-xl border border-border-default bg-canvas px-3.5 py-2 text-body font-semibold text-text-secondary"
                }
                onClick={() => setTab(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>

          {tab === "metadata" ? (
            <div className="grid gap-3 sm:grid-cols-2">
              <InfoTile label="Languages" value={selected.languages || "—"} />
              <InfoTile label="Description" value={selected.description || "—"} />
              <InfoTile label="Latest version" value={String(selected.latest_version ?? "—")} />
              <InfoTile label="Visibility" value={selected.visibility || "—"} />
              <div className="sm:col-span-2 flex flex-wrap gap-2">
                <ActionButton disabled title="API not available yet">
                  Edit template
                </ActionButton>
                <ActionButton variant="outline" disabled title="API not available yet">
                  Archive template
                </ActionButton>
              </div>
              <div className="sm:col-span-2 grid gap-2">
                <ApiNote>
                  Template edit and archive endpoints are not available yet. Current platform API
                  supports GET/POST /api/v1/platform/templates only. Detail payload does not
                  return voice, tools, instructions, or transfer rules after create.
                </ApiNote>
              </div>
            </div>
          ) : null}

          {tab === "visibility" ? (
            <div className="grid gap-3">
              <InfoTile label="Current visibility" value={selected.visibility || "—"} />
              <ApiNote>
                Visibility is set at create time (global, selected agencies, or internal). There
                is no PATCH endpoint to change visibility after create yet.
              </ApiNote>
            </div>
          ) : null}

          {tab === "versions" ? (
            <div className="grid gap-3">
              <InfoTile label="Latest version" value={String(selected.latest_version ?? "—")} />
              <ActionButton disabled title="API not available yet">
                Create new version
              </ActionButton>
              <ApiNote>
                Template versioning beyond v1 create is not exposed. There is no GET
                /platform/templates/{"{id}"}/versions or POST new-version route yet.
              </ApiNote>
            </div>
          ) : null}

          {tab === "install" ? (
            <div className="grid gap-3">
              <p className="m-0 text-body text-text-secondary">
                Agencies install an editable agent from an allowed template with:
              </p>
              <pre className="m-0 overflow-auto rounded-xl bg-canvas p-4 text-body-sm text-text-secondary">
                {`POST /api/v1/agency/agents
{
  "template_id": "${selected.id}",
  "customer_id": "<customer-uuid>",
  "display_name": "Agent name"
}`}
              </pre>
              <ApiNote>
                SA6-004 install/clone is agency-scoped (agents.manage). There is no platform route
                to install a template into an agency on behalf of a tenant yet.
              </ApiNote>
            </div>
          ) : null}
        </article>
      ) : (
        <p className="text-body text-text-muted">Select a template to inspect SA6 controls.</p>
      )}
    </section>
  );
}

function Field({
  label,
  name,
  defaultValue,
  required,
}: {
  label: string;
  name: string;
  defaultValue?: string;
  required?: boolean;
}) {
  return (
    <label className="m-0 grid gap-1.5 font-normal">
      <span className="text-body-sm text-text-muted">{label}</span>
      <input
        name={name}
        required={required}
        defaultValue={defaultValue}
        className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
      />
    </label>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border-default bg-canvas px-3 py-3">
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1 mb-0 font-semibold text-text-primary">{value}</p>
    </div>
  );
}
