# Agents, templates, and knowledge

Agents live in the Agency tenant database. New agents start `draft`. Production routing
requires `status=active` and a published version. Pause, suspend, archive, and unpublished
drafts fail closed (`agent_not_routable`). Number assignment is Phase 10; Pipecat
`/internal/telephony/v1/` is Phase 11.

Templates clone into an independent agent plus a frozen instruction snapshot. Instruction
precedence is Platform Safety → Template snapshot → Agency → Customer → Agent. Tools are
allowlisted (`tools` JSON + domain allowlist = SRS **AgentAction**; no separate Action ORM).
Prompts that look like credentials return `422 secret_in_prompt`.

Knowledge is ingested by Django. Sources start `queued`, move to `processing`, and become `ready` only after the vector upsert (Qdrant when `QDRANT_URL` is set, otherwise the in-process store). Failed upserts leave the source `failed`, never `ready`. File uploads (`md`, `txt`, `pdf`, `docx`, `html`, `csv`, `json`) are extracted server-side. URL ingest still requires extracted text; Django does not fetch remote URLs (SSRF). Payload `group_id` is sealed as `global`, `agency:{tenant_id}`, `customer:{customer_id}`, or `agent:{agent_id}`. Detach removes an agent link only. Deleting a source requires `confirm=true` when agents are attached (KB-004). Super Admin directory uses the control-plane `AgentIndex` and does not traverse tenant databases.

Call Handling interruption/barge-in is implemented in Pipecat, not as an agent-builder field.
