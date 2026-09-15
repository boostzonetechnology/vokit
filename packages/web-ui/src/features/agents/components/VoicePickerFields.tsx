import type { Portal } from "@/api";
import { ActionButton } from "@/components/ui/ActionButton";
import { useTtsVoices } from "@/features/agents/hooks/useTtsVoices";

export function VoicePickerFields({
  portal,
  voiceId,
  language,
  onVoiceIdChange,
  onLanguageChange,
  disabled,
}: {
  portal: Portal;
  voiceId: string;
  language: string;
  onVoiceIdChange: (voiceId: string) => void;
  onLanguageChange: (language: string) => void;
  disabled?: boolean;
}) {
  const { provider, voices, loading, error, reload } = useTtsVoices(portal);
  const selectDisabled = Boolean(disabled || loading || error || voices.length === 0);

  function onSelectVoice(nextId: string) {
    onVoiceIdChange(nextId);
    const match = voices.find((voice) => voice.id === nextId);
    if (match?.language) {
      onLanguageChange(match.language);
    }
  }

  return (
    <div className="grid min-w-0 gap-3">
      <div className="min-w-0 rounded-xl border border-border-default bg-canvas px-3 py-2.5">
        <p className="m-0 text-body-sm text-text-muted">Platform TTS</p>
        <p className="mt-1 mb-0 break-words font-semibold text-text-primary">
          {loading ? "Loading…" : provider || "Not available"}
        </p>
        {error ? (
          <p className="mt-2 mb-0 text-sm text-danger" role="alert">
            {error}
          </p>
        ) : null}
        {error || !voices.length ? (
          <div className="mt-2">
            <ActionButton type="button" variant="outline" disabled={loading} onClick={() => void reload()}>
              Retry voice list
            </ActionButton>
          </div>
        ) : null}
      </div>

      <label className="m-0 grid min-w-0 gap-1.5 font-normal">
        <span className="text-body-sm text-text-muted">Voice</span>
        <select
          value={voiceId}
          disabled={selectDisabled}
          onChange={(event) => onSelectVoice(event.target.value)}
          className="box-border w-full max-w-full min-w-0 rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
        >
          <option value="">
            {loading ? "Loading voices…" : voices.length ? "Select a voice…" : "No voices available"}
          </option>
          {voiceId && !voices.some((voice) => voice.id === voiceId) ? (
            <option value={voiceId}>Current voice (not in catalog)</option>
          ) : null}
          {voices.map((voice) => {
            const label = voice.name?.trim() || "Unnamed voice";
            const withLang = voice.language ? `${label} (${voice.language})` : label;
            return (
              <option key={voice.id} value={voice.id} title={voice.id}>
                {withLang.length > 56 ? `${withLang.slice(0, 53)}…` : withLang}
              </option>
            );
          })}
        </select>
        {!loading && !error && voices.length === 0 ? (
          <span className="text-sm text-text-muted">
            No voices returned for the active TTS vendor. Check platform provider settings.
          </span>
        ) : null}
      </label>

      <label className="m-0 grid min-w-0 gap-1.5 font-normal">
        <span className="text-body-sm text-text-muted">Language</span>
        <input
          value={language}
          disabled={disabled}
          onChange={(event) => onLanguageChange(event.target.value)}
          required
          placeholder="en"
          className="box-border w-full max-w-full min-w-0 rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body disabled:opacity-60"
        />
      </label>
    </div>
  );
}
