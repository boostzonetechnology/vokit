# Voice providers (STT / TTS / LLM)

Super Admin selects one STT, one TTS, and one LLM in platform settings. Vendor API keys are stored as Family B ciphertext in `platform_settings` (ADR-008 §4b). Pipecat receives the decrypted snapshot only on the frozen internal bootstrap contract. There is no React UI in this slice.

## Source of truth

| What | Where |
|---|---|
| Active vendors | `telephony.stt_provider`, `telephony.tts_provider`, `telephony.llm_provider` |
| Optional model names | `telephony.stt_model`, `telephony.tts_model`, `telephony.llm_model` |
| Vendor keys (secret) | `voice.{vendor}.api_key` |
| Default TTS voice if the agent has none | `ai.default_voice` |
| Agent voice | `voice_id` + `language` only. `voice_provider` is ignored at runtime |

Allowlists:

- STT / TTS: `deepgram`, `elevenlabs`, `cartesia`
- LLM: `openai`, `grok`, `anthropic`

Google remains in the Pipecat mapper but is not selectable in settings.

`VOICE_*` environment variables are **not** used for live selection. Keep them in `.env.example` only as unused leftovers.

## Save a key

`PATCH /api/v1/platform/settings` with `setting.update` and a required `reason`:

```json
{
  "key": "voice.cartesia.api_key",
  "value": "<plaintext once>",
  "reason": "lab cartesia key"
}
```

Django encrypts with salt `voice_provider_api_key` before MySQL. GET returns `value: null` and `has_value: true`. Audit `after_summary` is blank. Empty PATCH is rejected.

Rotation: PATCH the same key with the new plaintext. Changing `DJANGO_SECRET_KEY` invalidates these rows until re-entry (same as MFA / tenant vaults). See `docs/execution/runbooks/key-rotation.md`.

## Runtime

Bootstrap `providers.{stt,tts,llm}` uses the settings vendor + that vendor’s decrypted key (not one key per modality). TTS `voice_id` is the agent’s `voice_id`, else `ai.default_voice`. Agent `voice_provider` is not applied.

Lab bootstrap may still admit with empty keys (Pipecat fails later on a real call). `GET .../tts/voices` fails closed with `503` if the active TTS vendor or key is missing, `502` if the vendor HTTP call fails.

## TTS voice list

Official vendor HTTP, active TTS only:

- Cartesia `GET https://api.cartesia.ai/voices`
- ElevenLabs `GET https://api.elevenlabs.io/v1/voices`
- Deepgram `GET https://api.deepgram.com/v1/models` (TTS / Aura ids)

Normalized: `{ provider, voices: [{ id, name, language }] }`.

| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/platform/tts/voices` | platform `agent.view` or `setting.view` |
| GET | `/api/v1/agency/tts/voices` | agency `agent.view` |
| GET | `/api/v1/customer/tts/voices` | customer `agent.view` |

Publish still requires `voice_id` and `language`. It does not require `voice_provider`.

## Provider model list (settings UI)

Lists **models** for a specific vendor using that vendor’s stored Family B key. This is separate from TTS **voices** (`voice_id` for agents).

| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/platform/providers/{vendor}/models?capability=stt\|tts\|llm` | platform `setting.view` or `setting.update` (or super_admin) |

Normalized: `{ provider, capability, models: [{ id, name }] }`.

Source per vendor:

| Vendor | Capability | Source |
|---|---|---|
| OpenAI / Grok / Anthropic | LLM | Live vendor `/v1/models` (chat models only for OpenAI/Grok) |
| Deepgram | STT / TTS | Live `GET /v1/models` section |
| ElevenLabs | TTS | Live `GET /v1/models` where `can_do_text_to_speech` |
| ElevenLabs | STT | Live `GET /v1/models` Scribe / speech-to-text entries |
| Cartesia | STT / TTS | Documented model IDs (Cartesia has no list-models API). Key is probed via voices. Agent voices stay on `GET .../tts/voices` |

Fail-closed: `503` if vendor/capability invalid or key missing; `502` if vendor HTTP fails (clearer key/timeout messages).

`telephony.{stt,tts,llm}_model` is global per capability. Switching Active vendor must not keep another vendor’s model id as if it belonged to the new vendor.
