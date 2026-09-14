# Vokit Local Development

Greenfield local stack. Do not invent a second “demo tenant router.”

## 1. Prerequisites (target)

- Python 3.12+
- Node.js 22+
- MySQL 8
- Redis
- Rust 1.74+ (SIP Edge)
- uv or pip for Pipecat
- Docker optional for MySQL/Redis

Windows (current workspace) is supported for API/UI. Linux path casing must still be respected.

## 2. After proceed — intended local services

| Service | Port (local default) | Notes |
|---|---|---|
| Django API | 8000 | Bind 0.0.0.0 for VM/lab |
| Platform UI | 5173 | Vite |
| Agency UI | 5174 | |
| Customer UI | 5175 | |
| Redis | 6379 | |
| Control MySQL | 3306 | |
| Tenant A/B MySQL | 3307/3308 or same host different DB names | Two physical DBs required for isolation tests |
| Pipecat | 8100 | `/sip/media` |
| SIP Edge | 8090 HTTP | Private |
| Asterisk | lab config | See `deploy/asterisk` |
| Recording | TBD | Not Django :8000/media |
| Dummy payment processor | 8081 | Lab checkout. `packages/dummy-payment-processor` |
| Dummy KYC processor | 8082 | Lab KYC host. Documents stay here, not in Django |
| Qdrant | 6333 | Knowledge |

## 3. Voice lab (exists today)

Follow:

- `packages/pipecat-voice/README.md`
- `packages/vokit-sip-edge/README.md`
- `deploy/asterisk/README.md`

Tokens that must match:

- Edge `SIP_NODE_MEDIA_BASE_URL` `media_token`
- Pipecat `VOKIT_MEDIA_WS_TOKEN`
- Django `VOKIT_INTERNAL_TELEPHONY_TOKEN` / Edge control URL when API exists

## 4. Environment files

Commit only `.env.example`. Never commit `.env`.

Never put real processor, SIP, or DB passwords in docs or tickets.

Lab processors (optional, local only):

- Dummy payment: `packages/dummy-payment-processor` on `127.0.0.1:8081`. Match `SANDBOX_WEBHOOK_SECRET` with `apps/api/.env`. Customer pay uses `processor=sandbox` and opens `hosted_url`.
- Dummy KYC: `packages/dummy-kyc-processor` on `127.0.0.1:8082`. Match `KYC_WEBHOOK_SECRET`. Point `KYC_HOSTED_BASE_URL` at the dummy host. If Super Admin already saved KYC settings, update hosted URL there too. Verified webhook sets KYC Verified only; Super Admin still activates the agency.

Live STT/TTS/LLM vendors and API keys are **not** read from `VOICE_*` env. Super Admin PATCHes `telephony.{stt,tts,llm}_provider` and `voice.{vendor}.api_key` on `/api/v1/platform/settings` (encrypted at rest). See `docs/flows/VOICE-PROVIDERS.md`.

## 5. Isolation fixture

Local/CI must provision:

- Control-plane DB
- Agency A DB
- Agency B DB
- User A member of Agency A
- User B member of Agency B
- Same `call_id` UUID seeded in both tenant DBs

This fixture is mandatory before claiming tenant isolation.

## 6. What not to do locally

- Point both agencies at one shared business schema “for convenience”
- Serve recordings from `apps/api/media`
- Use Django Templates as a portal
- Copy old application code
