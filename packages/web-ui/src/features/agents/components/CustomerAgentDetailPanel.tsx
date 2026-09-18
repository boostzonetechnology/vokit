import { FormEvent, useEffect, useState, type ReactNode } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSectionSkeleton } from "@/components/ui/FormSectionSkeleton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import {
  agentStatusTone,
  canCustomerPause,
  canCustomerResume,
  formatBoolOnOff,
  formatBusinessHours,
  formatOptional,
  formatTools,
} from "@/features/agents/lib/customerAgentStatus";
import type { CustomerAgentDetail } from "@/features/agents/types";

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border-default bg-canvas px-3 py-3">
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1 mb-0 break-words font-semibold text-text-primary">{value}</p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="grid gap-3">
      <h3 className="m-0 text-body font-semibold text-text-primary">{title}</h3>
      {children}
    </section>
  );
}

function FieldBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border-default px-3 py-2">
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1 mb-0 whitespace-pre-wrap break-words text-body text-text-primary">
        {value}
      </p>
    </div>
  );
}

export function CustomerAgentDetailPanel({
  detail,
  detailLoading,
  busy,
  onPause,
  onResume,
  onSaveLimitedFields,
}: {
  detail: CustomerAgentDetail | null;
  detailLoading: boolean;
  busy: boolean;
  onPause: () => Promise<void>;
  onResume: () => Promise<void>;
  onSaveLimitedFields: (input: {
    greeting: string;
    instructions: string;
  }) => Promise<void>;
}) {
  const [showEdit, setShowEdit] = useState(false);
  const canEdit = Boolean(detail?.customer_can_edit);
  const locked = Boolean(detail?.status_locked);
  const showPause = canCustomerPause(detail);
  const showResume = canCustomerResume(detail);

  useEffect(() => {
    setShowEdit(false);
  }, [detail?.id]);

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) return;
    const form = new FormData(event.currentTarget);
    try {
      await onSaveLimitedFields({
        greeting: String(form.get("greeting") || ""),
        instructions: String(form.get("instructions") || ""),
      });
      setShowEdit(false);
    } catch {
      /* hook message */
    }
  }

  if (detailLoading && !detail) {
    return (
      <article className="min-w-0 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <FormSectionSkeleton fields={8} />
      </article>
    );
  }

  if (!detail) {
    return (
      <article className="min-w-0 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <h2 className="m-0 mb-3 text-section text-text-primary">Agent detail</h2>
        <p className="m-0 py-10 text-center text-body text-text-muted">
          Select an agent to monitor configuration and status.
        </p>
      </article>
    );
  }

  const overrideKeys = Object.keys(detail.tool_schema_overrides ?? {});

  return (
    <article className="min-w-0 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="m-0 break-words text-section text-text-primary">
            {detail.display_name || detail.id.slice(0, 8)}
          </h2>
        </div>
        <StatusBadge tone={agentStatusTone(detail.status)}>
          {detail.status || "—"}
        </StatusBadge>
      </div>

      <div className="grid gap-6">
        <div className="grid gap-3 sm:grid-cols-2">
          <InfoTile label="Assigned number" value={formatOptional(detail.assigned_e164)} />
          <InfoTile label="Type" value={formatOptional(detail.agent_type)} />
          <InfoTile
            label="Production routable"
            value={detail.production_routable ? "Yes" : "No"}
          />
          <InfoTile
            label="Edit permission"
            value={canEdit ? "Granted" : "Disabled by default"}
          />
          <InfoTile
            label="Status lock"
            value={
              locked
                ? `Locked${detail.status_actor ? ` · ${detail.status_actor}` : ""}`
                : "Unlocked"
            }
          />
          <InfoTile
            label="Versions"
            value={`draft ${formatOptional(detail.draft_version)} · published ${formatOptional(detail.published_version)}`}
          />
        </div>

        {(showPause || showResume || canEdit) && (
          <div className="flex flex-wrap gap-2">
            {showPause ? (
              <ActionButton
                variant="outline"
                disabled={busy}
                onClick={() => void onPause()}
              >
                Pause agent
              </ActionButton>
            ) : null}
            {showResume ? (
              <ActionButton disabled={busy} onClick={() => void onResume()}>
                Resume agent
              </ActionButton>
            ) : null}
            {canEdit ? (
              <ActionButton
                variant="secondary"
                disabled={busy}
                onClick={() => setShowEdit((value) => !value)}
              >
                {showEdit ? "Close editor" : "Edit greeting / instructions"}
              </ActionButton>
            ) : null}
          </div>
        )}

        {showEdit && canEdit ? (
          <form className="grid gap-3 rounded-xl border border-border-default bg-canvas p-4" onSubmit={(event) => void onSave(event)}>
            <FormField
              label="Greeting"
              name="greeting"
              defaultValue={detail.greeting || ""}
              key={`greeting-${detail.id}-${detail.greeting || ""}`}
            />
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Instructions</span>
              <textarea
                name="instructions"
                rows={5}
                defaultValue={detail.instructions || ""}
                key={`instructions-${detail.id}`}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Save allowed fields
            </ActionButton>
          </form>
        ) : null}

        <ApiNote>
          CU2-002/003 — edits and pause/resume are available only when the agency grants{" "}
          <code>customer_can_edit</code>. Only greeting and instructions are writable.
        </ApiNote>

        <Section title="Identity & routing">
          <div className="grid gap-2 sm:grid-cols-2">
            <FieldBlock label="Timezone" value={formatOptional(detail.timezone)} />
            <FieldBlock label="Language" value={formatOptional(detail.language)} />
            <FieldBlock
              label="Voice provider"
              value={formatOptional(detail.voice_provider)}
            />
            <FieldBlock
              label="Inbound"
              value={formatBoolOnOff(detail.inbound_enabled)}
            />
            <FieldBlock
              label="Outbound"
              value={formatBoolOnOff(detail.outbound_enabled)}
            />
            <FieldBlock
              label="Recording disclosure"
              value={formatBoolOnOff(detail.recording_disclosure)}
            />
            <FieldBlock
              label="Fallback behavior"
              value={formatOptional(detail.fallback_behavior)}
            />
            <FieldBlock
              label="Default transfer"
              value={formatOptional(detail.default_transfer_id)}
            />
            <FieldBlock
              label="Template"
              value={formatOptional(detail.template_id)}
            />
          </div>
        </Section>

        <Section title="Voice style & call timers">
          <div className="grid gap-2 sm:grid-cols-2">
            <FieldBlock
              label="Speaking style"
              value={formatOptional(detail.speaking_style)}
            />
            <FieldBlock
              label="Speaking speed"
              value={formatOptional(detail.speaking_speed)}
            />
            <FieldBlock
              label="Silence timeout (s)"
              value={formatOptional(detail.silence_timeout_seconds)}
            />
            <FieldBlock
              label="Max call duration (s)"
              value={formatOptional(detail.max_call_duration_seconds)}
            />
          </div>
        </Section>

        <Section title="Persona">
          <div className="grid gap-2">
            <FieldBlock label="Role" value={formatOptional(detail.role)} />
            <FieldBlock label="Goals" value={formatOptional(detail.goals)} />
            <FieldBlock label="Constraints" value={formatOptional(detail.constraints)} />
          </div>
        </Section>

        <Section title="Instructions & greetings">
          <div className="grid gap-2">
            <FieldBlock label="Greeting" value={formatOptional(detail.greeting)} />
            <FieldBlock label="Instructions" value={formatOptional(detail.instructions)} />
            <FieldBlock
              label="Template instructions"
              value={formatOptional(detail.template_instructions)}
            />
            <FieldBlock
              label="Voicemail greeting"
              value={formatOptional(detail.voicemail_greeting)}
            />
            <FieldBlock
              label="Outbound voicemail message"
              value={formatOptional(detail.outbound_voicemail_message)}
            />
          </div>
        </Section>

        <Section title="Call handling">
          <FieldBlock
            label="Business hours"
            value={formatBusinessHours(detail.business_hours)}
          />
        </Section>

        <Section title="Tools">
          <FieldBlock label="Enabled tools" value={formatTools(detail.tools)} />
          <FieldBlock
            label="Schema overrides"
            value={
              overrideKeys.length
                ? `${overrideKeys.length} override(s): ${overrideKeys.join(", ")}`
                : "None"
            }
          />
        </Section>
      </div>
    </article>
  );
}
