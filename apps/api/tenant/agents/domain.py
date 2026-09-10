from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime

from control_plane.risk.domain.types import AgentStatus


@dataclass(frozen=True, slots=True)
class TenantAgent:
    agent_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    display_name: str
    status: AgentStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None
    agent_type: str = "custom"
    timezone: str = "UTC"
    voice_provider: str = ""
    voice_id: str = ""
    language: str = ""
    greeting: str = ""
    fallback_behavior: str = ""
    inbound_enabled: bool = False
    outbound_enabled: bool = False
    recording_disclosure: bool | None = None
    instructions: str = ""
    template_instructions: str = ""
    tools: tuple[str, ...] = ()
    published_version: int | None = None
    draft_version: int = 1
    template_id: uuid.UUID | None = None
    customer_can_edit: bool = False
    business_hours: tuple[dict[str, object], ...] = ()
    voicemail_greeting: str = ""
    outbound_voicemail_message: str = ""
    default_transfer_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class AgentVersionRecord:
    version_id: uuid.UUID
    agent_id: uuid.UUID
    tenant_id: uuid.UUID
    version: int
    published: bool
    snapshot: str
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class InstructionLayerRecord:
    tenant_id: uuid.UUID
    scope: str
    owner_id: uuid.UUID
    body: str
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class KnowledgeSourceRecord:
    source_id: uuid.UUID
    tenant_id: uuid.UUID
    scope: str
    owner_id: uuid.UUID
    kind: str
    title: str
    body: str
    object_ref: str
    checksum: str
    status: str
    group_id: str
    customer_can_edit: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class KnowledgeAttachmentRecord:
    agent_id: uuid.UUID
    source_id: uuid.UUID
    tenant_id: uuid.UUID
    scope: str
    group_id: str


@dataclass(frozen=True, slots=True)
class TestSessionRecord:
    session_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    agent_id: uuid.UUID
    kind: str
    status: str
    created_at: datetime | None = None
    ended_at: datetime | None = None


def agent_config_json(agent: TenantAgent) -> str:
    payload = {
        "agent_type": agent.agent_type,
        "timezone": agent.timezone,
        "voice_provider": agent.voice_provider,
        "voice_id": agent.voice_id,
        "language": agent.language,
        "greeting": agent.greeting,
        "fallback_behavior": agent.fallback_behavior,
        "inbound_enabled": agent.inbound_enabled,
        "outbound_enabled": agent.outbound_enabled,
        "recording_disclosure": agent.recording_disclosure,
        "instructions": agent.instructions,
        "template_instructions": agent.template_instructions,
        "tools": list(agent.tools),
        "published_version": agent.published_version,
        "draft_version": agent.draft_version,
        "template_id": str(agent.template_id) if agent.template_id else None,
        "customer_can_edit": agent.customer_can_edit,
        "business_hours": list(agent.business_hours),
        "voicemail_greeting": agent.voicemail_greeting,
        "outbound_voicemail_message": agent.outbound_voicemail_message,
        "default_transfer_id": (
            str(agent.default_transfer_id) if agent.default_transfer_id else None
        ),
    }
    return json.dumps(payload)


def agent_from_config(
    *,
    agent_id: uuid.UUID,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    display_name: str,
    status: AgentStatus,
    created_at,
    updated_at,
    config_json: str | None,
    published_version: int | None = None,
    draft_version: int | None = None,
    template_id: uuid.UUID | None = None,
    customer_can_edit: bool | None = None,
) -> TenantAgent:
    data = {}
    if config_json:
        try:
            parsed = json.loads(config_json)
            if isinstance(parsed, dict):
                data = parsed
        except json.JSONDecodeError:
            data = {}
    raw_template = data.get("template_id")
    parsed_template = template_id
    if parsed_template is None and raw_template:
        parsed_template = uuid.UUID(str(raw_template))
    tools = data.get("tools") or []
    return TenantAgent(
        agent_id=agent_id,
        tenant_id=tenant_id,
        customer_id=customer_id,
        display_name=display_name,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        agent_type=str(data.get("agent_type") or "custom"),
        timezone=str(data.get("timezone") or "UTC"),
        voice_provider=str(data.get("voice_provider") or ""),
        voice_id=str(data.get("voice_id") or ""),
        language=str(data.get("language") or ""),
        greeting=str(data.get("greeting") or ""),
        fallback_behavior=str(data.get("fallback_behavior") or ""),
        inbound_enabled=bool(data.get("inbound_enabled") or False),
        outbound_enabled=bool(data.get("outbound_enabled") or False),
        recording_disclosure=data.get("recording_disclosure"),
        instructions=str(data.get("instructions") or ""),
        template_instructions=str(data.get("template_instructions") or ""),
        tools=tuple(str(item) for item in tools),
        published_version=published_version
        if published_version is not None
        else data.get("published_version"),
        draft_version=int(draft_version or data.get("draft_version") or 1),
        template_id=parsed_template,
        customer_can_edit=bool(customer_can_edit)
        if customer_can_edit is not None
        else bool(data.get("customer_can_edit") or False),
        business_hours=_hours(data.get("business_hours")),
        voicemail_greeting=str(data.get("voicemail_greeting") or ""),
        outbound_voicemail_message=str(data.get("outbound_voicemail_message") or ""),
        default_transfer_id=_optional_uuid(data.get("default_transfer_id")),
    )


def _hours(raw: object) -> tuple[dict[str, object], ...]:
    if type(raw) is not list:
        return ()
    return tuple(item for item in raw if type(item) is dict)


def _optional_uuid(raw: object) -> uuid.UUID | None:
    if not raw:
        return None
    try:
        return uuid.UUID(str(raw))
    except (ValueError, TypeError, AttributeError):
        return None


def agent_snapshot(agent: TenantAgent) -> str:
    payload = asdict(agent)
    payload["agent_id"] = str(agent.agent_id)
    payload["tenant_id"] = str(agent.tenant_id)
    payload["customer_id"] = str(agent.customer_id)
    payload["status"] = agent.status.value
    payload["template_id"] = str(agent.template_id) if agent.template_id else None
    payload["created_at"] = agent.created_at.isoformat() if agent.created_at else None
    payload["updated_at"] = agent.updated_at.isoformat() if agent.updated_at else None
    payload["tools"] = list(agent.tools)
    payload["default_transfer_id"] = (
        str(agent.default_transfer_id) if agent.default_transfer_id else None
    )
    payload["business_hours"] = list(agent.business_hours)
    return json.dumps(payload)
