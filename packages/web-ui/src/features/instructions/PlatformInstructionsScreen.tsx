import { FormEvent, useState, type ReactNode } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { usePlatformInstructions } from "./hooks/usePlatformInstructions";
import { INSTRUCTION_PRECEDENCE } from "./types";

type Tab = "global" | "template" | "precedence" | "versions";

function ApiNote({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-lg border border-dashed border-border-strong bg-canvas px-3 py-2 text-body-sm text-text-muted">
      {children}
    </p>
  );
}

export function PlatformInstructionsScreen() {
  const { draft, setDraft, error, message, loading, busy, reload, saveGlobal, dirty } =
    usePlatformInstructions();
  const [tab, setTab] = useState<Tab>("global");

  async function onSave(event: FormEvent) {
    event.preventDefault();
    try {
      await saveGlobal();
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "global", label: "Global (SA7-001)" },
    { id: "template", label: "Template (SA7-002)" },
    { id: "precedence", label: "Precedence (SA7-003)" },
    { id: "versions", label: "Versioning (SA7-004)" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Instructions
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA7-001–004 · Permission: agents.review
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

      {tab === "global" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 text-section text-text-primary">Platform safety instructions</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            GET/POST /api/v1/platform/instructions — each save creates a new GlobalInstruction
            revision on the server.
          </p>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading instructions…</p>
          ) : (
            <form className="grid gap-4" onSubmit={(event) => void onSave(event)}>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Instruction body</span>
                <textarea
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  rows={14}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 font-mono text-body"
                />
              </label>
              <div className="flex flex-wrap gap-2">
                <ActionButton type="submit" disabled={busy || !dirty}>
                  Save global instructions
                </ActionButton>
                <ActionButton
                  type="button"
                  variant="outline"
                  disabled={busy || !dirty}
                  onClick={() => void reload()}
                >
                  Discard draft
                </ActionButton>
              </div>
            </form>
          )}
        </article>
      ) : null}

      {tab === "template" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 text-section text-text-primary">Template instructions</h2>
          <p className="mt-1 mb-4 text-body text-text-secondary">
            Reusable template prompts are stored on template versions at create time (see
            Templates → Create → Template instructions).
          </p>
          <ApiNote>
            There is no separate GET/PATCH /platform/template-instructions API. Template
            instructions can only be set via POST /api/v1/platform/templates (instructions
            field). Editing template instructions after create is not available yet.
          </ApiNote>
          <div className="mt-4">
            <ActionButton disabled title="API not available yet">
              Manage template instruction library
            </ActionButton>
          </div>
        </article>
      ) : null}

      {tab === "precedence" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Inheritance precedence</h2>
          <p className="mt-0 mb-4 text-body-sm text-text-muted">
            Deterministic order documented by the agents control plane. Not configurable via
            API.
          </p>
          <ol className="m-0 grid list-decimal gap-3 pl-5">
            {INSTRUCTION_PRECEDENCE.map((item) => (
              <li key={item.layer} className="rounded-xl border border-border-default bg-canvas p-3">
                <p className="m-0 font-semibold text-text-primary">{item.layer}</p>
                <p className="mt-1 mb-0 text-body-sm text-text-muted">{item.source}</p>
                <p className="mt-1 mb-0 text-body text-text-secondary">{item.rule}</p>
              </li>
            ))}
          </ol>
          <div className="mt-4">
            <ApiNote>
              SA7-003 is enforced in the agent runtime, not exposed as a writable settings
              endpoint. This screen documents the fixed precedence only.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "versions" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Instruction revisions</h2>
          <p className="mt-0 mb-4 text-body text-text-secondary">
            Saving global instructions creates a new revision and publisher record server-side.
          </p>
          <ActionButton disabled title="API not available yet">
            View revision history
          </ActionButton>
          <div className="mt-4">
            <ApiNote>
              SA7-004 (Should): revision list with publisher, timestamp, and diff is not exposed.
              GET /api/v1/platform/instructions returns the current body only.
            </ApiNote>
          </div>
        </article>
      ) : null}
    </section>
  );
}
