import { FormEvent } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AgencyStackTextarea } from "@/features/agencies/components/AgencyStackField";
import type { AgencyNote } from "@/features/agencies/types";

export function AgencyNotesPanel({
  notes,
  busy,
  onAdd,
}: {
  notes: AgencyNote[];
  busy: boolean;
  onAdd: (input: { body: string; risk_flag: boolean }) => Promise<void>;
}) {
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await onAdd({
      body: String(form.get("body") || "").trim(),
      risk_flag: form.get("risk_flag") === "on",
    });
    event.currentTarget.reset();
  }

  return (
    <div className="grid w-full min-w-0 gap-5">
      <form className="grid w-full min-w-0 gap-3" onSubmit={(e) => void onSubmit(e)}>
        <AgencyStackTextarea
          label="Internal note"
          name="body"
          required
          rows={4}
          maxLength={2000}
          placeholder="Platform-only note visible to Super Admins"
        />
        <label className="m-0 flex w-full min-w-0 items-center gap-2.5 font-normal">
          <input type="checkbox" name="risk_flag" className="shrink-0" />
          <span className="text-body text-text-secondary">Mark as risk flag</span>
        </label>
        <div>
          <ActionButton type="submit" disabled={busy}>
            Add note
          </ActionButton>
        </div>
      </form>

      {notes.length === 0 ? (
        <p className="m-0 text-body text-text-muted">No internal notes yet.</p>
      ) : (
        <ul className="m-0 grid list-none gap-3 p-0">
          {notes.map((note) => (
            <li
              key={note.id}
              className="rounded-xl border border-border-default bg-canvas px-3.5 py-3.5"
            >
              <div className="mb-1.5 flex flex-wrap items-center gap-2">
                {note.risk_flag ? (
                  <StatusBadge tone="danger">Risk</StatusBadge>
                ) : (
                  <StatusBadge tone="neutral">Note</StatusBadge>
                )}
                <span className="text-body-sm text-text-muted">
                  {note.created_at ? new Date(note.created_at).toLocaleString() : "—"}
                </span>
              </div>
              <p className="m-0 whitespace-pre-wrap text-body text-text-secondary">{note.body}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
