import { FormEvent } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { AgencyStackTextarea } from "@/features/agencies/components/AgencyStackField";
import {
  CAPABILITY_FIELDS,
  defaultCapabilities,
  type AgencyCapabilities,
  type AgencyRecord,
} from "@/features/agencies/types";

export function AgencyCapabilitiesPanel({
  detail,
  busy,
  onSave,
}: {
  detail: AgencyRecord;
  busy: boolean;
  onSave: (input: { capabilities: AgencyCapabilities; reason: string }) => Promise<void>;
}) {
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail.capabilities) return;
    const form = new FormData(event.currentTarget);
    if (form.get("confirm") !== "on") return;
    const reason = String(form.get("reason") || "").trim();
    if (!reason) return;
    const next = { ...defaultCapabilities() };
    for (const field of CAPABILITY_FIELDS) {
      next[field.key] = form.get(field.key) === "on";
    }
    await onSave({ capabilities: next, reason });
  }

  return (
    <form className="grid w-full min-w-0 gap-4" onSubmit={(e) => void onSubmit(e)}>
      <div className="grid gap-2 sm:grid-cols-2">
        {CAPABILITY_FIELDS.map((field) => (
          <label
            key={field.key}
            className="m-0 flex min-w-0 items-center gap-2.5 rounded-xl border border-border-default bg-canvas px-3 py-3 font-normal"
          >
            <input
              type="checkbox"
              name={field.key}
              defaultChecked={Boolean(detail.capabilities?.[field.key])}
              className="shrink-0"
            />
            <span className="min-w-0 text-body text-text-secondary">{field.label}</span>
          </label>
        ))}
      </div>

      <AgencyStackTextarea
        label="Reason (required)"
        name="reason"
        required
        rows={3}
        placeholder="Why are these capability gates changing?"
      />

      <label className="m-0 flex w-full min-w-0 items-start gap-2.5 font-normal">
        <input type="checkbox" name="confirm" required className="mt-1 shrink-0" />
        <span className="text-body text-text-secondary">
          I confirm these capability changes. Turning off existing customer services blocks new
          production calls only.
        </span>
      </label>

      <div>
        <ActionButton type="submit" disabled={busy}>
          Save capabilities
        </ActionButton>
      </div>
    </form>
  );
}
