# Agents, templates, and knowledge

Agents live in the Agency tenant database. New agents start `draft`. Production routing
requires `status=active` and a published version. Pause, suspend, archive, and unpublished
drafts fail closed (`agent_not_routable`). Number assignment is Phase 10; Pipecat
`/internal/telephony/v1/` is Phase 11.

Templates clone into an independent agent plus a frozen instruction snapshot. Instruction
precedence is Platform Safety → Template snapshot → Agency → Customer → Agent. Tools are
allowlisted. Prompts that look like credentials return `422 secret_in_prompt`.

Knowledge is ingested by Django (hash embedding + Qdrant write, or in-process memory when
`QDRANT_URL` is empty). Payload `group_id` is sealed as `global`, `agency:{tenant_id}`,
`customer:{customer_id}`, or `agent:{agent_id}`. URL/file sources require extracted text;
Django does not fetch remote URLs. Super Admin directory uses the control-plane
`AgentIndex` and does not traverse tenant databases.
