import { FormEvent, useEffect, useMemo, useState, type ReactNode } from "react";
import { Eye, EyeOff } from "lucide-react";

import { isApiError } from "@/api";
import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { getTtsVoices } from "@/features/agents/services/ttsVoices.service";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import {
  getProviderModels,
  type ProviderModelOption,
} from "@/features/settings/services/providerModels.service";
import type { SettingRow } from "@/features/settings/types";
import {
  CAPABILITY_MODEL_KEY,
  CAPABILITY_PROVIDER_KEY,
  VENDOR_CARDS,
  capabilityLabel,
  type VendorCardDef,
  type VoiceCapability,
} from "@/features/settings/voice.constants";

type ProvidersSettingsPanelProps = {
  byKey: Map<string, SettingRow>;
  busy: boolean;
  onSaveBatch: (
    updates: Array<{ key: string; value: unknown; reason: string }>,
  ) => Promise<void>;
};

function settingString(byKey: Map<string, SettingRow>, key: string): string {
  const value = byKey.get(key)?.value;
  if (value == null) return "";
  return String(value);
}

function Fieldset({
  legend,
  children,
}: {
  legend: string;
  children: ReactNode;
}) {
  return (
    <fieldset className="m-0 min-w-0 overflow-hidden rounded-xl border border-border-default px-3 pb-3 pt-1">
      <legend className="px-1 text-body-sm font-semibold text-text-secondary">{legend}</legend>
      {children}
    </fieldset>
  );
}

function modelOptionLabel(row: ProviderModelOption): string {
  if (row.name && row.name !== row.id) {
    const combined = `${row.name} (${row.id})`;
    return combined.length > 48 ? `${combined.slice(0, 45)}…` : combined;
  }
  return row.id.length > 48 ? `${row.id.slice(0, 45)}…` : row.id;
}

function VendorProviderCard({
  vendor,
  byKey,
  busy,
  activeByCapability,
  onSaveBatch,
}: {
  vendor: VendorCardDef;
  byKey: Map<string, SettingRow>;
  busy: boolean;
  activeByCapability: Record<VoiceCapability, string>;
  onSaveBatch: ProvidersSettingsPanelProps["onSaveBatch"];
}) {
  const keyRow = byKey.get(vendor.apiKeyKey);
  const hasKey = Boolean(keyRow?.has_value);

  const [apiKey, setApiKey] = useState("");
  const [reason, setReason] = useState("");
  const [activeCaps, setActiveCaps] = useState<Record<VoiceCapability, boolean>>({
    stt: false,
    tts: false,
    llm: false,
  });
  const [models, setModels] = useState<Record<VoiceCapability, string>>({
    stt: "",
    tts: "",
    llm: "",
  });
  const [cardError, setCardError] = useState("");
  const [cardMessage, setCardMessage] = useState("");
  const [voiceProbe, setVoiceProbe] = useState("");
  const [probing, setProbing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [catalogByCap, setCatalogByCap] = useState<
    Partial<Record<VoiceCapability, ProviderModelOption[]>>
  >({});
  const [catalogStatus, setCatalogStatus] = useState<
    Partial<Record<VoiceCapability, string>>
  >({});
  const [loadingCatalog, setLoadingCatalog] = useState(false);

  useEffect(() => {
    setActiveCaps({
      stt: activeByCapability.stt === vendor.code,
      tts: activeByCapability.tts === vendor.code,
      llm: activeByCapability.llm === vendor.code,
    });
    setModels({
      stt: settingString(byKey, CAPABILITY_MODEL_KEY.stt),
      tts: settingString(byKey, CAPABILITY_MODEL_KEY.tts),
      llm: settingString(byKey, CAPABILITY_MODEL_KEY.llm),
    });
    setApiKey("");
    setShowApiKey(false);
  }, [vendor.code, activeByCapability, byKey]);

  async function loadModelCatalogs(opts?: { force?: boolean }) {
    const canLoad = Boolean(opts?.force || hasKey);
    if (!canLoad) {
      setCatalogByCap({});
      const next: Partial<Record<VoiceCapability, string>> = {};
      for (const cap of vendor.capabilities) {
        next[cap] = "Save an API key on this card to load models from the vendor.";
      }
      setCatalogStatus(next);
      return;
    }
    setLoadingCatalog(true);
    const nextCatalog: Partial<Record<VoiceCapability, ProviderModelOption[]>> = {};
    const nextStatus: Partial<Record<VoiceCapability, string>> = {};
    await Promise.all(
      vendor.capabilities.map(async (cap) => {
        try {
          const data = await getProviderModels(vendor.code, cap);
          nextCatalog[cap] = data.models;
          nextStatus[cap] = data.models.length
            ? `${data.models.length} models loaded from ${vendor.title}.`
            : "Credentials accepted, but the vendor returned no models for this capability.";
        } catch (cause) {
          nextCatalog[cap] = [];
          nextStatus[cap] = isApiError(cause)
            ? cause.message || "Could not load models."
            : "Could not load models.";
        }
      }),
    );
    setCatalogByCap(nextCatalog);
    setCatalogStatus(nextStatus);
    // Drop foreign/stale telephony.*_model values that belong to another vendor.
    setModels((prev) => {
      const next = { ...prev };
      for (const cap of vendor.capabilities) {
        const catalog = nextCatalog[cap] || [];
        const current = prev[cap].trim();
        if (current && catalog.length > 0 && !catalog.some((row) => row.id === current)) {
          next[cap] = "";
        }
      }
      return next;
    });
    setLoadingCatalog(false);
  }

  useEffect(() => {
    void loadModelCatalogs();
    // Reload when this card's stored key presence changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vendor.code, hasKey]);

  async function probeTtsVoices() {
    if (!vendor.capabilities.includes("tts")) return;
    if (activeByCapability.tts !== vendor.code && !activeCaps.tts) {
      setVoiceProbe("Activate TTS on this card and save to load the voice catalog.");
      return;
    }
    if (!hasKey && !apiKey.trim()) {
      setVoiceProbe("Voices unavailable: missing API key for this TTS vendor.");
      return;
    }
    setProbing(true);
    setVoiceProbe("");
    try {
      const data = await getTtsVoices("platform");
      if (data.provider && data.provider !== vendor.code) {
        setVoiceProbe(
          `Active platform TTS is ${data.provider}. Save this card as Active TTS to load its voices.`,
        );
      } else {
        setVoiceProbe(
          data.voices.length
            ? `Voice catalog ready (${data.voices.length} voices). Agents can pick voice_id from this list.`
            : "Credentials accepted, but the vendor returned no voices.",
        );
      }
    } catch (cause) {
      setVoiceProbe(
        isApiError(cause)
          ? cause.message || "Could not load voice catalog."
          : "Could not load voice catalog.",
      );
    } finally {
      setProbing(false);
    }
  }

  useEffect(() => {
    if (!vendor.capabilities.includes("tts")) return;
    if (activeByCapability.tts !== vendor.code || !hasKey) {
      setVoiceProbe(
        hasKey
          ? "API key is set. Mark TTS Active and save to use this vendor."
          : "Voices unavailable: missing credentials for this TTS vendor.",
      );
      return;
    }
    void probeTtsVoices();
    // Probe when server state says this vendor is active TTS with a key.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vendor.code, activeByCapability.tts, hasKey]);

  function toggleActive(cap: VoiceCapability, checked: boolean) {
    setActiveCaps((prev) => ({ ...prev, [cap]: checked }));
  }

  async function onSave(event: FormEvent) {
    event.preventDefault();
    setCardError("");
    setCardMessage("");
    const trimmedReason = reason.trim() || `Update ${vendor.title} provider settings`;
    const updates: Array<{ key: string; value: unknown; reason: string }> = [];

    for (const cap of vendor.capabilities) {
      const providerKey = CAPABILITY_PROVIDER_KEY[cap];
      const currentlyActive = activeByCapability[cap] === vendor.code;
      const wantActive = activeCaps[cap];
      if (currentlyActive && !wantActive) {
        setCardError(
          `Cannot turn off ${capabilityLabel(cap)} here. Open another ${capabilityLabel(cap)} vendor card, mark it Active, and save.`,
        );
        return;
      }
      if (wantActive && !currentlyActive) {
        updates.push({ key: providerKey, value: vendor.code, reason: trimmedReason });
      }
      if (wantActive) {
        const modelKey = CAPABILITY_MODEL_KEY[cap];
        const catalog = catalogByCap[cap] || [];
        const selected = models[cap].trim();
        let nextModel = selected;
        if (catalog.length > 0) {
          if (!catalog.some((row) => row.id === selected)) {
            nextModel = "";
          }
        } else if (!currentlyActive) {
          // Activating this vendor: never keep another vendor's global model id.
          nextModel = "";
        }
        const prevModel = settingString(byKey, modelKey);
        if (nextModel !== prevModel) {
          updates.push({ key: modelKey, value: nextModel, reason: trimmedReason });
        }
      }
    }

    if (apiKey.trim()) {
      updates.push({
        key: vendor.apiKeyKey,
        value: apiKey.trim(),
        reason: trimmedReason,
      });
    }

    if (!updates.length) {
      setCardError("Nothing to save. Change Active/model or enter a new API key.");
      return;
    }

    setSaving(true);
    try {
      await onSaveBatch(updates);
      setApiKey("");
      setCardMessage("Saved.");
      if (apiKey.trim()) {
        await loadModelCatalogs({ force: true });
      } else if (hasKey) {
        await loadModelCatalogs();
      }
      if (vendor.capabilities.includes("tts") && (activeCaps.tts || apiKey.trim())) {
        await probeTtsVoices();
      }
    } catch (cause) {
      setCardError(isApiError(cause) ? cause.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  const localBusy = busy || saving;

  return (
    <form
      onSubmit={(event) => void onSave(event)}
      className="flex h-full min-w-0 flex-col gap-4 overflow-hidden rounded-2xl border border-border-default bg-surface p-4 shadow-subtle"
    >
      <header className="min-w-0">
        <h3 className="m-0 text-[1.15rem] font-bold text-text-primary">{vendor.title}</h3>
        <div className="mt-2 flex flex-wrap gap-1.5">
          <span className="rounded-full bg-canvas px-2 py-0.5 font-mono text-xs text-text-muted">
            {vendor.code}
          </span>
          {vendor.capabilities.map((cap) => (
            <span
              key={cap}
              className="rounded-full bg-canvas px-2 py-0.5 font-mono text-xs text-text-muted"
            >
              {cap}
            </span>
          ))}
          {hasKey ? <StatusBadge tone="success">API key set</StatusBadge> : null}
        </div>
      </header>

      <Fieldset legend="Credentials (shared for this vendor)">
        <label className="m-0 grid min-w-0 gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">
            API key{" "}
            <span className="font-normal text-text-muted">
              {hasKey
                ? "(stored encrypted — paste a new key to rotate)"
                : "(required to load models)"}
            </span>
          </span>
          <div className="relative min-w-0">
            <input
              type={showApiKey ? "text" : "password"}
              autoComplete="new-password"
              value={apiKey}
              disabled={localBusy}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder={hasKey ? "••••••••••••" : "Paste API key"}
              className="w-full min-w-0 rounded-xl border border-border-default bg-surface py-2.5 pl-3 pr-12 text-body"
            />
            <button
              type="button"
              disabled={localBusy}
              aria-label={showApiKey ? "Hide API key" : "Show API key"}
              title={showApiKey ? "Hide API key" : "Show API key"}
              onClick={() => setShowApiKey((prev) => !prev)}
              className="absolute inset-y-0 right-1 inline-flex size-10 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-canvas hover:text-text-primary disabled:opacity-40"
            >
              {showApiKey ? <EyeOff className="size-4" aria-hidden /> : <Eye className="size-4" aria-hidden />}
            </button>
          </div>
        </label>
        <label className="mt-3 m-0 grid min-w-0 gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Reason (audit)</span>
          <input
            value={reason}
            disabled={localBusy}
            onChange={(event) => setReason(event.target.value)}
            placeholder={`Update ${vendor.title}`}
            className="w-full min-w-0 rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
          />
        </label>
      </Fieldset>

      <Fieldset legend="Capabilities">
        <div className="grid min-w-0 gap-3">
          {vendor.capabilities.map((cap) => {
            const isActive = activeCaps[cap];
            return (
              <div
                key={cap}
                className="min-w-0 overflow-hidden rounded-xl border border-border-default bg-canvas px-3 py-3"
              >
                <p className="m-0 text-body font-semibold text-text-primary">
                  {capabilityLabel(cap)}
                </p>
                <label className="mt-2 flex items-center gap-2 text-sm text-text-primary">
                  <input
                    type="checkbox"
                    checked={isActive}
                    disabled={localBusy}
                    onChange={(event) => toggleActive(cap, event.target.checked)}
                  />
                  Active (platform uses this vendor)
                </label>
                <div className="mt-2">
                  <StatusBadge tone={isActive ? "success" : "danger"}>
                    {isActive ? "In use" : "Off"}
                  </StatusBadge>
                </div>
                <label className="mt-3 m-0 grid min-w-0 gap-1.5 font-normal">
                  <span className="text-body-sm text-text-muted">Model (optional)</span>
                  <select
                    value={
                      (catalogByCap[cap] || []).some((row) => row.id === models[cap])
                        ? models[cap]
                        : ""
                    }
                    disabled={localBusy || loadingCatalog || !isActive || !hasKey}
                    onChange={(event) =>
                      setModels((prev) => ({ ...prev, [cap]: event.target.value }))
                    }
                    className="box-border w-full max-w-full min-w-0 rounded-xl border border-border-default bg-surface px-3 py-2 text-body disabled:opacity-60"
                  >
                    <option value="">
                      {!hasKey
                        ? "Save API key first"
                        : loadingCatalog
                          ? "Loading…"
                          : isActive
                            ? "— none —"
                            : "Activate to select"}
                    </option>
                    {(catalogByCap[cap] || []).map((row) => (
                      <option key={row.id} value={row.id}>
                        {modelOptionLabel(row)}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="mt-2 mb-0 break-words text-xs text-text-muted">
                  {loadingCatalog
                    ? "Loading model catalog…"
                    : catalogStatus[cap] ||
                      (cap === "tts"
                        ? probing
                          ? "Checking voice catalog…"
                          : voiceProbe
                        : null)}
                </p>
                {cap === "tts" ? (
                  <p className="mt-1 mb-0 break-words text-xs text-text-muted">
                    Model is the TTS engine id. Agent voices (voice_id) come from Refresh voices —
                    not this dropdown.
                    {voiceProbe && catalogStatus[cap]
                      ? ` ${probing ? "Checking voice catalog…" : voiceProbe}`
                      : null}
                  </p>
                ) : null}
              </div>
            );
          })}
        </div>
      </Fieldset>

      {cardError ? (
        <p className="m-0 text-sm text-danger" role="alert">
          {cardError}
        </p>
      ) : null}
      {cardMessage ? (
        <p className="m-0 text-sm text-text-brand" role="status">
          {cardMessage}
        </p>
      ) : null}

      <div className="mt-auto flex min-w-0 flex-wrap gap-2">
        <ActionButton type="submit" disabled={localBusy}>
          {saving ? "Saving…" : `Save ${vendor.title}`}
        </ActionButton>
        <ActionButton
          type="button"
          variant="outline"
          disabled={localBusy || loadingCatalog || !hasKey}
          onClick={() => void loadModelCatalogs()}
        >
          Refresh models
        </ActionButton>
        {vendor.capabilities.includes("tts") ? (
          <ActionButton
            type="button"
            variant="outline"
            disabled={localBusy || probing}
            onClick={() => void probeTtsVoices()}
          >
            Refresh voices
          </ActionButton>
        ) : null}
      </div>
    </form>
  );
}

export function ProvidersSettingsPanel({
  byKey,
  busy,
  onSaveBatch,
}: ProvidersSettingsPanelProps) {
  const activeByCapability = useMemo(
    () => ({
      stt: settingString(byKey, CAPABILITY_PROVIDER_KEY.stt),
      tts: settingString(byKey, CAPABILITY_PROVIDER_KEY.tts),
      llm: settingString(byKey, CAPABILITY_PROVIDER_KEY.llm),
    }),
    [byKey],
  );

  const defaultVoice = settingString(byKey, "ai.default_voice");
  const timeout = settingString(byKey, "telephony.default_timeout_seconds");
  const emailSender = settingString(byKey, "notifications.email_sender");

  const [extraReason, setExtraReason] = useState("");
  const [extraDefaultVoice, setExtraDefaultVoice] = useState(defaultVoice);
  const [extraTimeout, setExtraTimeout] = useState(timeout);
  const [extraEmail, setExtraEmail] = useState(emailSender);

  useEffect(() => {
    setExtraDefaultVoice(defaultVoice);
    setExtraTimeout(timeout);
    setExtraEmail(emailSender);
  }, [defaultVoice, timeout, emailSender]);

  async function onSaveExtras(event: FormEvent) {
    event.preventDefault();
    const reason = extraReason.trim() || "Update shared provider defaults";
    const updates: Array<{ key: string; value: unknown; reason: string }> = [];
    if (extraDefaultVoice !== defaultVoice) {
      updates.push({ key: "ai.default_voice", value: extraDefaultVoice, reason });
    }
    if (extraTimeout !== timeout) {
      updates.push({
        key: "telephony.default_timeout_seconds",
        value: Number(extraTimeout) || 0,
        reason,
      });
    }
    if (extraEmail !== emailSender) {
      updates.push({ key: "notifications.email_sender", value: extraEmail, reason });
    }
    if (!updates.length) return;
    await onSaveBatch(updates);
    setExtraReason("");
  }

  return (
    <div className="grid gap-5">
      <div>
        <h2 className="m-0 text-section text-text-primary">AI providers</h2>
        <p className="mt-1 mb-0 text-body text-text-muted">
          One Active vendor per capability (STT, TTS, LLM). API keys are encrypted and never shown
          after save. After you save a key, Model loads from that vendor’s API (Refresh models).
          For TTS agents, use Refresh voices for the voice_id catalog.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <span className="rounded-full border border-border-default bg-canvas px-3 py-1 text-body-sm text-text-secondary">
          STT: <strong className="text-text-primary">{activeByCapability.stt || "—"}</strong>
        </span>
        <span className="rounded-full border border-border-default bg-canvas px-3 py-1 text-body-sm text-text-secondary">
          TTS: <strong className="text-text-primary">{activeByCapability.tts || "—"}</strong>
        </span>
        <span className="rounded-full border border-border-default bg-canvas px-3 py-1 text-body-sm text-text-secondary">
          LLM: <strong className="text-text-primary">{activeByCapability.llm || "—"}</strong>
        </span>
      </div>

      <div className="grid min-w-0 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {VENDOR_CARDS.map((vendor) => (
          <VendorProviderCard
            key={vendor.code}
            vendor={vendor}
            byKey={byKey}
            busy={busy}
            activeByCapability={activeByCapability}
            onSaveBatch={onSaveBatch}
          />
        ))}
      </div>

      <form
        onSubmit={(event) => void onSaveExtras(event)}
        className="grid gap-3 rounded-2xl border border-border-default bg-surface p-4 shadow-subtle"
      >
        <h3 className="m-0 text-body font-semibold text-text-primary">Shared defaults</h3>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Default TTS voice id</span>
            <input
              value={extraDefaultVoice}
              disabled={busy}
              onChange={(event) => setExtraDefaultVoice(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Telephony timeout (seconds)</span>
            <input
              value={extraTimeout}
              disabled={busy}
              onChange={(event) => setExtraTimeout(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Email sender</span>
            <input
              value={extraEmail}
              disabled={busy}
              onChange={(event) => setExtraEmail(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
        </div>
        <label className="m-0 grid max-w-md gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Reason</span>
          <input
            value={extraReason}
            disabled={busy}
            onChange={(event) => setExtraReason(event.target.value)}
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
          />
        </label>
        <div>
          <ActionButton type="submit" disabled={busy}>
            Save shared defaults
          </ActionButton>
        </div>
      </form>

      <ApiNote>
        Embedding is not part of the V1 voice catalog. Unchecking Active does not clear the platform
        provider until you Activate another vendor and save. Clearing a stored API key is not
        supported by the settings API (empty PATCH is rejected) — rotate by saving a new key.
      </ApiNote>
    </div>
  );
}
