import { FormEvent, useEffect, useState, type ReactNode } from "react";

import type { Portal } from "@/api";
import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { BusinessHoursEditor, isValidHhMm } from "@/features/agents/components/BusinessHoursEditor";
import { VoicePickerFields } from "@/features/agents/components/VoicePickerFields";
import {
  ALLOWED_AGENT_TOOLS,
  FALLBACK_BEHAVIORS,
  MAX_CALL_DURATION_RANGE,
  SILENCE_TIMEOUT_RANGE,
  SPEAKING_SPEED_RANGE,
  type BusinessHoursWindow,
  type PlatformAgentDetail,
} from "@/features/agents/types";
import type { TransferDestination } from "@/features/transfers/types";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <fieldset className="m-0 grid min-w-0 gap-3 rounded-xl border border-border-default px-3 py-3">
      <legend className="px-1 text-body-sm font-semibold text-text-primary">{title}</legend>
      {children}
    </fieldset>
  );
}

export function AgentConfigureForm({
  portal,
  detail,
  busy,
  disabled,
  transfers = [],
  onSubmit,
}: {
  portal: Portal;
  detail: PlatformAgentDetail;
  busy: boolean;
  disabled?: boolean;
  transfers?: TransferDestination[];
  onSubmit: (patch: Record<string, unknown>) => Promise<void>;
}) {
  const locked = Boolean(disabled);
  const [displayName, setDisplayName] = useState(detail.display_name || "");
  const [timezone, setTimezone] = useState(detail.timezone || "UTC");
  const [voiceId, setVoiceId] = useState(detail.voice_id || "");
  const [language, setLanguage] = useState(detail.language || "");
  const [speakingStyle, setSpeakingStyle] = useState(detail.speaking_style || "");
  const [speakingSpeed, setSpeakingSpeed] = useState(
    String(detail.speaking_speed ?? SPEAKING_SPEED_RANGE.default),
  );
  const [role, setRole] = useState(detail.role || "");
  const [goals, setGoals] = useState(detail.goals || "");
  const [constraints, setConstraints] = useState(detail.constraints || "");
  const [greeting, setGreeting] = useState(detail.greeting || "");
  const [instructions, setInstructions] = useState(detail.instructions || "");
  const [fallback, setFallback] = useState(
    FALLBACK_BEHAVIORS.includes(
      (detail.fallback_behavior || "message") as (typeof FALLBACK_BEHAVIORS)[number],
    )
      ? detail.fallback_behavior || "message"
      : "message",
  );
  const [inbound, setInbound] = useState(Boolean(detail.inbound_enabled));
  const [outbound, setOutbound] = useState(Boolean(detail.outbound_enabled));
  const [recording, setRecording] = useState(Boolean(detail.recording_disclosure));
  const [hours, setHours] = useState<BusinessHoursWindow[]>(detail.business_hours ?? []);
  const [voicemailGreeting, setVoicemailGreeting] = useState(detail.voicemail_greeting || "");
  const [outboundVoicemail, setOutboundVoicemail] = useState(
    detail.outbound_voicemail_message || "",
  );
  const [silenceTimeout, setSilenceTimeout] = useState(
    String(detail.silence_timeout_seconds ?? SILENCE_TIMEOUT_RANGE.default),
  );
  const [maxDuration, setMaxDuration] = useState(
    String(detail.max_call_duration_seconds ?? MAX_CALL_DURATION_RANGE.default),
  );
  const [defaultTransferId, setDefaultTransferId] = useState(
    detail.default_transfer_id || "",
  );
  const [tools, setTools] = useState<string[]>(detail.tools ?? []);
  const [localError, setLocalError] = useState("");

  useEffect(() => {
    setDisplayName(detail.display_name || "");
    setTimezone(detail.timezone || "UTC");
    setVoiceId(detail.voice_id || "");
    setLanguage(detail.language || "");
    setSpeakingStyle(detail.speaking_style || "");
    setSpeakingSpeed(String(detail.speaking_speed ?? SPEAKING_SPEED_RANGE.default));
    setRole(detail.role || "");
    setGoals(detail.goals || "");
    setConstraints(detail.constraints || "");
    setGreeting(detail.greeting || "");
    setInstructions(detail.instructions || "");
    setFallback(
      FALLBACK_BEHAVIORS.includes(
        (detail.fallback_behavior || "message") as (typeof FALLBACK_BEHAVIORS)[number],
      )
        ? detail.fallback_behavior || "message"
        : "message",
    );
    setInbound(Boolean(detail.inbound_enabled));
    setOutbound(Boolean(detail.outbound_enabled));
    setRecording(Boolean(detail.recording_disclosure));
    setHours(detail.business_hours ?? []);
    setVoicemailGreeting(detail.voicemail_greeting || "");
    setOutboundVoicemail(detail.outbound_voicemail_message || "");
    setSilenceTimeout(String(detail.silence_timeout_seconds ?? SILENCE_TIMEOUT_RANGE.default));
    setMaxDuration(String(detail.max_call_duration_seconds ?? MAX_CALL_DURATION_RANGE.default));
    setDefaultTransferId(detail.default_transfer_id || "");
    setTools(detail.tools ?? []);
    setLocalError("");
  }, [detail]);

  const customerTransfers = transfers.filter(
    (row) =>
      !detail.customer_id ||
      !row.customer_id ||
      row.customer_id === detail.customer_id,
  );

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLocalError("");

    if (hours.length > 0) {
      const bad = hours.some((row) => !isValidHhMm(row.start) || !isValidHhMm(row.end));
      if (bad) {
        setLocalError("Business hours must use valid HH:MM values.");
        return;
      }
    }

    const speed = Number(speakingSpeed);
    const silence = Number(silenceTimeout);
    const maxCall = Number(maxDuration);
    if (
      Number.isNaN(speed) ||
      speed < SPEAKING_SPEED_RANGE.min ||
      speed > SPEAKING_SPEED_RANGE.max
    ) {
      setLocalError(
        `Speaking speed must be ${SPEAKING_SPEED_RANGE.min}–${SPEAKING_SPEED_RANGE.max}.`,
      );
      return;
    }
    if (
      Number.isNaN(silence) ||
      silence < SILENCE_TIMEOUT_RANGE.min ||
      silence > SILENCE_TIMEOUT_RANGE.max
    ) {
      setLocalError(
        `Silence timeout must be ${SILENCE_TIMEOUT_RANGE.min}–${SILENCE_TIMEOUT_RANGE.max} seconds.`,
      );
      return;
    }
    if (
      Number.isNaN(maxCall) ||
      maxCall < MAX_CALL_DURATION_RANGE.min ||
      maxCall > MAX_CALL_DURATION_RANGE.max
    ) {
      setLocalError(
        `Max call duration must be ${MAX_CALL_DURATION_RANGE.min}–${MAX_CALL_DURATION_RANGE.max} seconds.`,
      );
      return;
    }

    const patch: Record<string, unknown> = {
      display_name: displayName.trim(),
      timezone: timezone.trim() || "UTC",
      voice_id: voiceId,
      language,
      speaking_style: speakingStyle.trim(),
      speaking_speed: speed,
      role: role.trim(),
      goals: goals.trim(),
      constraints: constraints.trim(),
      greeting: greeting.trim(),
      instructions: instructions.trim(),
      fallback_behavior: fallback,
      inbound_enabled: inbound,
      outbound_enabled: outbound,
      recording_disclosure: recording,
      business_hours: hours,
      voicemail_greeting: voicemailGreeting.trim(),
      outbound_voicemail_message: outboundVoicemail.trim(),
      silence_timeout_seconds: silence,
      max_call_duration_seconds: maxCall,
      tools,
    };
    if (defaultTransferId) {
      patch.default_transfer_id = defaultTransferId;
    }

    await onSubmit(patch);
  }

  function toggleTool(name: string) {
    setTools((prev) =>
      prev.includes(name) ? prev.filter((item) => item !== name) : [...prev, name],
    );
  }

  return (
    <form className="grid min-w-0 gap-4" onSubmit={(event) => void handleSubmit(event)}>
      <Section title="Identity">
        <FormField
          label="Display name"
          name="display_name"
          value={displayName}
          disabled={locked}
          onChange={(event) => setDisplayName(event.target.value)}
        />
        <FormField
          label="Timezone"
          name="timezone"
          value={timezone}
          disabled={locked}
          placeholder="UTC"
          onChange={(event) => setTimezone(event.target.value)}
        />
        {detail.agent_type ? (
          <p className="m-0 text-sm text-text-muted">Type: {detail.agent_type}</p>
        ) : null}
      </Section>

      <Section title="Voice & language">
        <VoicePickerFields
          portal={portal}
          voiceId={voiceId}
          language={language}
          onVoiceIdChange={setVoiceId}
          onLanguageChange={setLanguage}
          disabled={busy || locked}
        />
        <FormField
          label="Speaking style"
          name="speaking_style"
          value={speakingStyle}
          disabled={locked}
          placeholder="e.g. warm, concise"
          onChange={(event) => setSpeakingStyle(event.target.value)}
        />
        <FormField
          label={`Speaking speed (${SPEAKING_SPEED_RANGE.min}–${SPEAKING_SPEED_RANGE.max})`}
          name="speaking_speed"
          type="number"
          step="0.1"
          min={SPEAKING_SPEED_RANGE.min}
          max={SPEAKING_SPEED_RANGE.max}
          value={speakingSpeed}
          disabled={locked}
          onChange={(event) => setSpeakingSpeed(event.target.value)}
        />
      </Section>

      <Section title="Persona & instructions">
        <FormField
          label="Role"
          name="role"
          value={role}
          disabled={locked}
          onChange={(event) => setRole(event.target.value)}
        />
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Goals</span>
          <textarea
            rows={2}
            value={goals}
            disabled={locked}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => setGoals(event.target.value)}
          />
        </label>
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Constraints</span>
          <textarea
            rows={2}
            value={constraints}
            disabled={locked}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => setConstraints(event.target.value)}
          />
        </label>
        <FormField
          label="Greeting"
          name="greeting"
          value={greeting}
          disabled={locked}
          onChange={(event) => setGreeting(event.target.value)}
        />
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Instructions</span>
          <textarea
            rows={4}
            value={instructions}
            disabled={locked}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => setInstructions(event.target.value)}
          />
        </label>
      </Section>

      <Section title="Call handling">
        <div className="flex flex-wrap gap-4">
          <label className="m-0 flex items-center gap-2 font-normal text-body">
            <input
              type="checkbox"
              checked={inbound}
              disabled={locked}
              onChange={(event) => setInbound(event.target.checked)}
            />
            Inbound enabled
          </label>
          <label className="m-0 flex items-center gap-2 font-normal text-body">
            <input
              type="checkbox"
              checked={outbound}
              disabled={locked}
              onChange={(event) => setOutbound(event.target.checked)}
            />
            Outbound enabled
          </label>
          <label className="m-0 flex items-center gap-2 font-normal text-body">
            <input
              type="checkbox"
              checked={recording}
              disabled={locked}
              onChange={(event) => setRecording(event.target.checked)}
            />
            Recording disclosure
          </label>
        </div>
        <BusinessHoursEditor
          value={hours}
          onChange={setHours}
          disabled={locked}
          resetKey={`${detail.id}-${detail.draft_version ?? 0}`}
        />
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Fallback behavior</span>
          <select
            value={fallback}
            disabled={locked}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => setFallback(event.target.value)}
          >
            <option value="message">message — voicemail / stay on line</option>
            <option value="transfer">transfer — default transfer destination</option>
            <option value="hangup">hangup — end the call</option>
          </select>
        </label>
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Voicemail greeting (inbound)</span>
          <textarea
            rows={2}
            value={voicemailGreeting}
            disabled={locked}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => setVoicemailGreeting(event.target.value)}
          />
        </label>
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Outbound voicemail message</span>
          <textarea
            rows={2}
            value={outboundVoicemail}
            disabled={locked}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => setOutboundVoicemail(event.target.value)}
          />
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          <FormField
            label={`Silence timeout (s, ${SILENCE_TIMEOUT_RANGE.min}–${SILENCE_TIMEOUT_RANGE.max})`}
            name="silence_timeout"
            type="number"
            min={SILENCE_TIMEOUT_RANGE.min}
            max={SILENCE_TIMEOUT_RANGE.max}
            value={silenceTimeout}
            disabled={locked}
            onChange={(event) => setSilenceTimeout(event.target.value)}
          />
          <FormField
            label={`Max call duration (s, ${MAX_CALL_DURATION_RANGE.min}–${MAX_CALL_DURATION_RANGE.max})`}
            name="max_duration"
            type="number"
            min={MAX_CALL_DURATION_RANGE.min}
            max={MAX_CALL_DURATION_RANGE.max}
            value={maxDuration}
            disabled={locked}
            onChange={(event) => setMaxDuration(event.target.value)}
          />
        </div>
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Default transfer destination</span>
          <select
            value={defaultTransferId}
            disabled={locked}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
            onChange={(event) => setDefaultTransferId(event.target.value)}
          >
            <option value="">None</option>
            {customerTransfers.map((row) => (
              <option key={row.id} value={row.id}>
                {row.label || row.id.slice(0, 8)}
                {row.kind ? ` · ${row.kind}` : ""}
              </option>
            ))}
          </select>
          {!customerTransfers.length ? (
            <span className="text-sm text-text-muted">
              No destinations for this customer. Create them under Transfers.
            </span>
          ) : null}
        </label>
      </Section>

      <Section title="Tools / actions">
        <p className="m-0 text-sm text-text-muted">
          Allowlisted AgentAction tools only. Secrets never go in prompts.
        </p>
        <div className="grid gap-2 sm:grid-cols-2">
          {ALLOWED_AGENT_TOOLS.map((name) => (
            <label key={name} className="m-0 flex items-center gap-2 font-normal text-body">
              <input
                type="checkbox"
                checked={tools.includes(name)}
                disabled={locked}
                onChange={() => toggleTool(name)}
              />
              {name}
            </label>
          ))}
        </div>
      </Section>

      {localError ? (
        <p className="m-0 text-danger" role="alert">
          {localError}
        </p>
      ) : null}

      <ActionButton type="submit" disabled={busy || locked}>
        Save configuration
      </ActionButton>
    </form>
  );
}
