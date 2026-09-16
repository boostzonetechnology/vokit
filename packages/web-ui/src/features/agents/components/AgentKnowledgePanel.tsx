import { useEffect, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import type { AgentKnowledgeAttachment } from "@/features/agents/types";
import type { KnowledgeRecord } from "@/features/knowledge/types";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "ready") return "success";
  if (value === "queued" || value === "processing") return "warning";
  if (value === "failed" || value === "stale") return "danger";
  return "neutral";
}

export function AgentKnowledgePanel({
  agentId,
  customerId: _customerId,
  busy,
  disabled,
  attached,
  available,
  loading,
  onReload,
  onAttach,
  onDetach,
}: {
  agentId: string;
  customerId?: string;
  busy: boolean;
  disabled?: boolean;
  attached: AgentKnowledgeAttachment[];
  available: KnowledgeRecord[];
  loading: boolean;
  onReload: () => void;
  onAttach: (sourceId: string) => Promise<void>;
  onDetach: (sourceId: string) => Promise<void>;
}) {
  const [sourceId, setSourceId] = useState("");
  const attachedIds = new Set(attached.map((row) => row.source_id));

  const attachable = available.filter((row) => {
    if (!row.id || attachedIds.has(row.id)) return false;
    const status = (row.status ?? "").toLowerCase();
    if (status && status !== "ready") return false;
    return true;
  });

  useEffect(() => {
    setSourceId("");
  }, [agentId]);

  return (
    <div className="grid gap-3 rounded-xl border border-border-default px-3 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="m-0 text-body-sm font-semibold text-text-primary">Knowledge</h3>
          <p className="mt-1 mb-0 text-sm text-text-muted">
            Attach ready sources to this agent (AG3-002 / VKT-067). Ingest new sources under
            Knowledge.
          </p>
        </div>
        <ActionButton type="button" variant="outline" disabled={busy || loading} onClick={onReload}>
          Refresh
        </ActionButton>
      </div>

      {loading ? (
        <p className="m-0 text-body text-text-muted">Loading attachments…</p>
      ) : attached.length === 0 ? (
        <p className="m-0 text-body text-text-muted">No knowledge attached yet.</p>
      ) : (
        <ul className="m-0 grid list-none gap-2 p-0">
          {attached.map((row) => (
            <li
              key={row.source_id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
            >
              <div className="min-w-0">
                <p className="m-0 font-medium text-text-primary">
                  {row.title || row.source_id.slice(0, 8)}
                </p>
                <p className="m-0 text-sm text-text-muted">
                  {row.scope || "—"} · {row.source_id.slice(0, 8)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge tone={statusTone(row.status)}>{row.status || "—"}</StatusBadge>
                <ActionButton
                  type="button"
                  variant="outline"
                  disabled={busy || disabled}
                  onClick={() => void onDetach(row.source_id)}
                >
                  Detach
                </ActionButton>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap items-end gap-2">
        <label className="m-0 grid min-w-[12rem] flex-1 gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Attach source</span>
          <select
            value={sourceId}
            disabled={busy || disabled || attachable.length === 0}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => setSourceId(event.target.value)}
          >
            <option value="">Select ready source…</option>
            {attachable.map((row) => (
              <option key={row.id} value={row.id}>
                {row.title || row.id.slice(0, 8)} · {row.scope}
              </option>
            ))}
          </select>
        </label>
        <ActionButton
          type="button"
          disabled={busy || disabled || !sourceId}
          onClick={() => {
            if (!sourceId) return;
            void onAttach(sourceId).then(() => setSourceId(""));
          }}
        >
          Attach
        </ActionButton>
      </div>
    </div>
  );
}
