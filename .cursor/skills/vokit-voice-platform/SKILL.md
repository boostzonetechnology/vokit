# Vokit Voice Platform Skill

## When to use
Use for Asterisk, SIP Edge, Pipecat, WebSocket media, STT, TTS, LLM, transfers, call lifecycle, agent runtime and realtime performance.

## Procedure
1. Inspect existing wire contracts first.
2. Trace caller -> Asterisk -> SIP Edge -> media service -> STT/LLM/TTS -> Django events/end/transfer.
3. Identify realtime vs control-plane responsibilities.
4. Keep Django authoritative for provider configuration, billing, agents and call records.
5. Define timeout, cancellation, retry, backpressure and safe fallback behavior.
6. Validate codec/sample-rate/interruption behavior.
7. Validate agent tool allowlist and tenant-scoped knowledge retrieval.
8. Add call lifecycle and provider-event idempotency tests.
9. Measure latency and resource consumption before optimizing.

## Production gate
A realtime change is not complete until routing, bootstrap, media, termination, transfer and dependency-failure paths are tested and observable.
