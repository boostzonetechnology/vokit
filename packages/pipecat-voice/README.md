# Pipecat realtime voice peer (Phase 13)

Self-hosted media WebSocket server that speaks the **existing** Vokit edge contract.
Django remains the source of truth for providers, billing, agents, and call records.

## Role

```text
Caller → Asterisk → vokit-sip-edge → this service (/sip/media)
                                      → STT → LLM → TTS
                                      → Django bootstrap / events / end
```

Rust `vokit-sip-edge` is unchanged. Cutover is an env URL:

```env
# Edge — point at Pipecat (this process)
SIP_NODE_MEDIA_BASE_URL=ws://127.0.0.1:8100/sip/media?media_token=SAME_AS_VOKIT_MEDIA_WS_TOKEN

# Rollback — point back at Django
# SIP_NODE_MEDIA_BASE_URL=ws://127.0.0.1:8000/sip/media?media_token=SAME_AS_VOKIT_MEDIA_WS_TOKEN
```

## Requirements

- Python 3.11+
- Official extras: `pipecat-ai[websocket,webrtc,silero,deepgram,elevenlabs,cartesia,openai,google,anthropic,grok]` plus `fastembed` for local knowledge query embeddings.

Install (official command style):

```powershell
cd packages/pipecat-voice
uv sync
```

or:

```powershell
pip install -e ".[dev]"
```

## Run

```powershell
cd packages/pipecat-voice
copy .env.example .env
# edit tokens to match Django + edge
uv run uvicorn vokit_pipecat_voice.app:app --host 0.0.0.0 --port 8100
```

Health: `GET http://127.0.0.1:8100/health`

## Implement-time notes

- Current `FrameSerializer` has `serialize` / `deserialize` / `setup`. `FrameSerializerType` is not required on pipecat-ai 1.7.x.
- Pipeline run uses official `PipelineWorker` + `WorkerRunner` (not the deprecated `PipelineTask` / `PipelineRunner` aliases).
- Interruptions are enabled by default on user-turn start strategies; the serializer emits `{"type":"clear"}` on `InterruptionFrame`.
- FastAPI transport already yields mixed binary + text; the custom serializer uses that.
- Bootstrap runs in the FastAPI route after the edge `start` JSON (not inside `deserialize`).
- Wire stays 8 kHz μ-law (OQ-036). Pipeline TTS PCM is 24 kHz; the serializer resamples on the way out (official Pipecat telephony + TTS sample-rate split).
- Outbound edge sessions echo μ-law and do not start an AI pipeline.
- If Django is unreachable at bootstrap or mid-call heartbeat, the call fails closed (no grace period).
