# Telephony incident

1. Django remains SoT. Do not rename `/internal/telephony/v1/*`.
2. Missing service token → 401. User cookies are not a substitute.
3. Unpublished/paused agents are not admitted.
4. If Django is down, Pipecat must fail closed (no guessed tenant).
5. Drain calls before rolling Pipecat. Point Edge at last known-good media URL on rollback.
6. Transfers and voicemail metadata stay in the tenant DB; raw audio stays on the recording plane.

Evidence: voice/media API tests; Phase 17 voice matrix catalog.
