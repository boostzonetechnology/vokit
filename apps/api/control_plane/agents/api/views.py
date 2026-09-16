from __future__ import annotations

from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.agents.application.builder import (
    UNSET,
    ConfigureAgentCommand,
    _load_agent,
    assert_agent_routable,
)
from control_plane.agents.application.diagnostics import agent_diagnostics, assigned_e164_map
from control_plane.agents.application.knowledge import IngestKnowledgeCommand, source_impact
from control_plane.agents.application.resolve import resolve_for_agent
from control_plane.agents.application.templates import CreateTemplateCommand
from control_plane.agents.domain.policies import parse_agent_status
from control_plane.agents.domain.types import TemplateStatus, TemplateVisibility
from control_plane.agents.infrastructure.container import (
    agent_index,
    attach_knowledge,
    clone_agent,
    configure_agent,
    create_template,
    delete_knowledge,
    detach_knowledge,
    global_instructions,
    global_knowledge,
    ingest_knowledge,
    install_template,
    pause_agent,
    publish_agent,
    save_instruction,
    set_agent_status,
    start_test_session,
    template_versions,
    templates,
)
from control_plane.customers.infrastructure.container import customer_index
from control_plane.identity.api.auth import (
    parse_optional_uuid,
    parse_uuid,
    require_agency_perm,
    require_customer_perm,
    require_platform_perm,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.integrations.domain.policies import merged_tool_schemas
from control_plane.risk.application.create_agent import CreateAgentCommand
from control_plane.risk.infrastructure.container import create_agent, tenant_agents
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page
from tenant.agents.domain import TenantAgent


def _agent_payload(row: TenantAgent) -> dict[str, object]:
    return {
        "id": str(row.agent_id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "display_name": row.display_name,
        "status": row.status.value,
        "agent_type": row.agent_type,
        "timezone": row.timezone,
        "voice_provider": row.voice_provider,
        "voice_id": row.voice_id,
        "language": row.language,
        "greeting": row.greeting,
        "fallback_behavior": row.fallback_behavior,
        "inbound_enabled": row.inbound_enabled,
        "outbound_enabled": row.outbound_enabled,
        "recording_disclosure": row.recording_disclosure,
        "instructions": row.instructions,
        "template_instructions": row.template_instructions,
        "tools": list(row.tools),
        "published_version": row.published_version,
        "draft_version": row.draft_version,
        "status_locked": bool(row.status_locked),
        "status_actor": row.status_actor,
        "template_id": str(row.template_id) if row.template_id else None,
        "customer_can_edit": row.customer_can_edit,
        "business_hours": list(row.business_hours),
        "voicemail_greeting": row.voicemail_greeting,
        "outbound_voicemail_message": row.outbound_voicemail_message,
        "default_transfer_id": (
            str(row.default_transfer_id) if row.default_transfer_id else None
        ),
        "speaking_style": row.speaking_style,
        "speaking_speed": row.speaking_speed,
        "role": row.role,
        "goals": row.goals,
        "constraints": row.constraints,
        "silence_timeout_seconds": row.silence_timeout_seconds,
        "max_call_duration_seconds": row.max_call_duration_seconds,
        "tool_schema_overrides": dict(row.tool_schema_overrides or {}),
        "tool_schemas": merged_tool_schemas(row.tools, row.tool_schema_overrides),
        "production_routable": bool(
            row.status.value == "active" and row.published_version is not None
        ),
    }


def _index_payload(row, *, assigned_e164: str | None = None) -> dict[str, object]:
    return {
        "id": str(row.id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "display_name": row.display_name,
        "status": row.status.value,
        "agent_type": row.agent_type,
        "published_version": row.published_version,
        "status_locked": bool(row.status_locked),
        "status_actor": row.status_actor,
        "assigned_e164": assigned_e164,
        "production_routable": bool(
            row.status.value == "active" and row.published_version is not None
        ),
    }


def _load_platform_agent(agent_id: str) -> TenantAgent:
    return _load_agent(tenant_agents(), parse_uuid(agent_id, field="agent_id"), None, True)


def _set_platform_status(request: Request, agent_id: str, status: str | None = None) -> Response:
    context = require_platform_perm(request, "agent.update")
    target = status if status is not None else str(request.data.get("status") or "")
    agent = set_agent_status().execute(
        agent_id=parse_uuid(agent_id, field="agent_id"),
        status=target,
        reason=str(request.data.get("reason") or ""),
        actor_id=context.user.id,
        actor_role=context.membership.role,
    )
    return success(_agent_payload(agent))


def _template_payload(row) -> dict[str, object]:
    version = template_versions().latest(row.id)
    return {
        "id": str(row.id),
        "name": row.name,
        "industry": row.industry,
        "use_case": row.use_case,
        "description": row.description,
        "languages": row.languages,
        "visibility": row.visibility.value,
        "status": row.status.value,
        "latest_version": version.version if version else None,
    }


def _bool_or_none(data: dict, name: str):
    if name not in data:
        return None
    raw = data.get(name)
    if type(raw) is not bool:
        raise DomainError("validation_error", f"{name} must be a boolean.")
    return raw


def _configure_command(
    agent_id, data: dict, *, tenant_id, privileged: bool
) -> ConfigureAgentCommand:
    tools = data.get("tools")
    return ConfigureAgentCommand(
        agent_id=agent_id,
        actor_tenant_id=tenant_id,
        privileged=privileged,
        display_name=None if "display_name" not in data else str(data.get("display_name") or ""),
        agent_type=None if "agent_type" not in data else str(data.get("agent_type") or ""),
        timezone=None if "timezone" not in data else str(data.get("timezone") or ""),
        voice_provider=None
        if "voice_provider" not in data
        else str(data.get("voice_provider") or ""),
        voice_id=None if "voice_id" not in data else str(data.get("voice_id") or ""),
        language=None if "language" not in data else str(data.get("language") or ""),
        greeting=None if "greeting" not in data else str(data.get("greeting") or ""),
        fallback_behavior=None
        if "fallback_behavior" not in data
        else str(data.get("fallback_behavior") or ""),
        inbound_enabled=_bool_or_none(data, "inbound_enabled"),
        outbound_enabled=_bool_or_none(data, "outbound_enabled"),
        recording_disclosure=_bool_or_none(data, "recording_disclosure"),
        instructions=None if "instructions" not in data else str(data.get("instructions") or ""),
        tools=None if tools is None else tuple(str(item) for item in tools),
        customer_can_edit=_bool_or_none(data, "customer_can_edit"),
        business_hours=None
        if "business_hours" not in data
        else tuple(item for item in (data.get("business_hours") or []) if type(item) is dict),
        voicemail_greeting=None
        if "voicemail_greeting" not in data
        else str(data.get("voicemail_greeting") or ""),
        outbound_voicemail_message=None
        if "outbound_voicemail_message" not in data
        else str(data.get("outbound_voicemail_message") or ""),
        default_transfer_id=_optional_uuid(data, "default_transfer_id"),
        speaking_style=None
        if "speaking_style" not in data
        else str(data.get("speaking_style") or ""),
        speaking_speed=UNSET if "speaking_speed" not in data else data.get("speaking_speed"),
        role=None if "role" not in data else str(data.get("role") or ""),
        goals=None if "goals" not in data else str(data.get("goals") or ""),
        constraints=None if "constraints" not in data else str(data.get("constraints") or ""),
        silence_timeout_seconds=UNSET
        if "silence_timeout_seconds" not in data
        else data.get("silence_timeout_seconds"),
        max_call_duration_seconds=UNSET
        if "max_call_duration_seconds" not in data
        else data.get("max_call_duration_seconds"),
        tool_schema_overrides=UNSET
        if "tool_schema_overrides" not in data
        else data.get("tool_schema_overrides"),
    )


def _file_from_request(request: Request) -> tuple[bytes | None, str, str]:
    upload = request.FILES.get("file") if getattr(request, "FILES", None) is not None else None
    if upload is None:
        return None, "", ""
    return upload.read(), str(getattr(upload, "name", "") or ""), str(
        getattr(upload, "content_type", "") or ""
    )


def _confirm_delete(request: Request) -> bool:
    raw = request.query_params.get("confirm")
    if raw in (None, "") and hasattr(request, "data"):
        raw = request.data.get("confirm") if request.data is not None else None
    return str(raw or "").strip().lower() in {"1", "true", "yes"}


def _knowledge_list_item(row) -> dict[str, object]:
    return {
        "id": str(row.source_id),
        "title": row.title,
        "scope": row.scope,
        "kind": row.kind,
        "status": row.status,
        "group_id": row.group_id,
    }


def _optional_uuid(data: dict, name: str):
    if name not in data:
        return None
    raw = data.get(name)
    if raw in (None, ""):
        return None
    return parse_uuid(str(raw), field=name)


class PlatformAgentCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        limit, offset = parse_page(
            request.query_params.get("limit"), request.query_params.get("offset")
        )
        status_raw = str(request.query_params.get("status") or "").strip()
        status = parse_agent_status(status_raw) if status_raw else None
        agent_type = str(request.query_params.get("agent_type") or "").strip() or None
        rows, page = page_slice(
            agent_index().list(
                tenant_id=parse_optional_uuid(
                    request.query_params.get("agency_id"), field="agency_id"
                ),
                customer_id=parse_optional_uuid(
                    request.query_params.get("customer_id"), field="customer_id"
                ),
                status=status,
                agent_type=agent_type,
            ),
            offset,
            limit,
        )
        assigned = assigned_e164_map([row.id for row in rows])
        return success(
            [_index_payload(row, assigned_e164=assigned.get(row.id)) for row in rows],
            page=page,
        )

    def post(self, request: Request) -> Response:
        require_platform_perm(request, "agent.update")
        agent = create_agent().execute(
            CreateAgentCommand(
                customer_id=parse_uuid(request.data.get("customer_id"), field="customer_id"),
                display_name=str(request.data.get("display_name") or ""),
                actor_tenant_id=None,
                privileged=True,
            )
        )
        return success(_agent_payload(agent), status=201)


class PlatformAgentDetailView(CsrfAPIView):
    def get(self, request: Request, agent_id: str) -> Response:
        require_platform_perm(request, "agent.view")
        agent = _load_platform_agent(agent_id)
        assigned = assigned_e164_map([agent.agent_id])
        payload = _agent_payload(agent)
        payload["assigned_e164"] = assigned.get(agent.agent_id)
        return success(payload)

    def patch(self, request: Request, agent_id: str) -> Response:
        require_platform_perm(request, "agent.update")
        agent = configure_agent().execute(
            _configure_command(
                parse_uuid(agent_id, field="agent_id"),
                dict(request.data),
                tenant_id=None,
                privileged=True,
            )
        )
        return success(_agent_payload(agent))


class PlatformAgentPublishView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        require_platform_perm(request, "agent.update")
        agent = publish_agent().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            actor_tenant_id=None,
            privileged=True,
        )
        return success(_agent_payload(agent))


class PlatformAgentStatusView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        return _set_platform_status(request, agent_id)


class PlatformAgentPauseView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        return _set_platform_status(request, agent_id, "paused")


class PlatformAgentArchiveView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        return _set_platform_status(request, agent_id, "archived")


class PlatformAgentDisableView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        return _set_platform_status(request, agent_id, "suspended")


class PlatformAgentCloneView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        require_platform_perm(request, "agent.update")
        agent = clone_agent().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            actor_tenant_id=None,
            privileged=True,
            customer_id=parse_uuid(request.data.get("customer_id"), field="customer_id"),
            display_name=str(request.data.get("display_name") or "") or None,
            greeting=None
            if "greeting" not in request.data
            else str(request.data.get("greeting") or ""),
            system_prompt=None
            if "system_prompt" not in request.data
            else str(request.data.get("system_prompt") or ""),
        )
        return success(_agent_payload(agent), status=201)


class PlatformAgentDiagnosticsView(CsrfAPIView):
    def get(self, request: Request, agent_id: str) -> Response:
        require_platform_perm(request, "agent.view")
        return success(agent_diagnostics(_load_platform_agent(agent_id)))


class PlatformTemplateCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        limit, offset = parse_page(
            request.query_params.get("limit"), request.query_params.get("offset")
        )
        rows, page = page_slice(templates().list(), offset, limit)
        return success([_template_payload(row) for row in rows], page=page)

    def post(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        selected = tuple(
            parse_uuid(item, field="selected_tenant_ids")
            for item in (request.data.get("selected_agency_ids") or [])
        )
        template, _version = create_template().execute(
            CreateTemplateCommand(
                name=str(request.data.get("name") or ""),
                industry=str(request.data.get("industry") or ""),
                use_case=str(request.data.get("use_case") or ""),
                description=str(request.data.get("description") or ""),
                languages=str(request.data.get("languages") or "en"),
                visibility=str(request.data.get("visibility") or "global"),
                selected_tenant_ids=selected,
                agent_type=str(request.data.get("agent_type") or "custom"),
                instructions=str(request.data.get("instructions") or ""),
                voice_provider=str(request.data.get("voice_provider") or ""),
                voice_id=str(request.data.get("voice_id") or ""),
                language=str(request.data.get("language") or "en"),
                tools=tuple(str(item) for item in (request.data.get("tools") or [])),
                fallback_behavior=str(request.data.get("fallback_behavior") or "message"),
            )
        )
        return success(_template_payload(template), status=201)


class PlatformInstructionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        return success({"body": global_instructions().get()})

    def post(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        from control_plane.agents.domain.policies import assert_no_secrets

        body = str(request.data.get("body") or "")
        assert_no_secrets(body, field="instructions")
        return success({"body": global_instructions().save(body)})


class PlatformKnowledgeView(CsrfAPIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        agency_id = parse_optional_uuid(
            request.query_params.get("agency_id"), field="agency_id"
        )
        if agency_id is not None:
            rows = [
                {**_knowledge_list_item(row), "agency_id": str(agency_id)}
                for row in tenant_agents().list_knowledge(agency_id)
            ]
            return success(rows)
        rows = [
            {
                "id": str(item.source_id),
                "title": item.title,
                "scope": "global",
                "kind": item.kind,
                "status": item.status,
                "group_id": item.group_id,
            }
            for item in global_knowledge().list()
        ]
        return success(rows)

    def post(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        from uuid import UUID

        file_bytes, filename, content_type = _file_from_request(request)
        result = ingest_knowledge().execute(
            IngestKnowledgeCommand(
                tenant_id=UUID("00000000-0000-7000-8000-000000000009"),
                scope="global",
                owner_id=UUID("00000000-0000-7000-8000-000000000009"),
                title=str(request.data.get("title") or ""),
                body=str(request.data.get("body") or ""),
                kind=str(request.data.get("kind") or "text"),
                object_ref=str(request.data.get("object_ref") or ""),
                privileged=True,
                filename=filename,
                content_type=content_type,
                file_bytes=file_bytes,
            )
        )
        return success(result, status=201)


class PlatformKnowledgeSourceView(CsrfAPIView):
    def delete(self, request: Request, source_id: str) -> Response:
        context = require_platform_perm(request, "agent.update")
        result = delete_knowledge().execute(
            source_id=parse_uuid(source_id, field="source_id"),
            actor_tenant_id=None,
            privileged=True,
            confirm=_confirm_delete(request),
            actor_id=context.user.id,
            actor_role=context.membership.role,
        )
        return success(result)


class AgencyAgentCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        limit, offset = parse_page(
            request.query_params.get("limit"), request.query_params.get("offset")
        )
        customer_id = parse_optional_uuid(
            request.query_params.get("customer_id"), field="customer_id"
        )
        rows, page = page_slice(tenant_agents().list_agents(tenant_id, customer_id), offset, limit)
        return success([_agent_payload(row) for row in rows], page=page)

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.create")
        tenant_id = context.membership.tenant_id
        template_id = request.data.get("template_id")
        if template_id:
            agent = install_template().execute(
                template_id=parse_uuid(template_id, field="template_id"),
                customer_id=parse_uuid(request.data.get("customer_id"), field="customer_id"),
                display_name=str(request.data.get("display_name") or ""),
                actor_tenant_id=tenant_id,
                privileged=False,
            )
            return success(_agent_payload(agent), status=201)
        agent = create_agent().execute(
            CreateAgentCommand(
                customer_id=parse_uuid(request.data.get("customer_id"), field="customer_id"),
                display_name=str(request.data.get("display_name") or ""),
                actor_tenant_id=tenant_id,
                privileged=False,
            )
        )
        return success(_agent_payload(agent), status=201)


class AgencyAgentDetailView(CsrfAPIView):
    def get(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        agent = tenant_agents().get_agent(tenant_id, parse_uuid(agent_id, field="agent_id"))
        if agent is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return success(_agent_payload(agent))

    def patch(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.update")
        agent = configure_agent().execute(
            _configure_command(
                parse_uuid(agent_id, field="agent_id"),
                dict(request.data),
                tenant_id=context.membership.tenant_id,
                privileged=False,
            )
        )
        return success(_agent_payload(agent))


class AgencyAgentPublishView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.update")
        agent = publish_agent().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            actor_tenant_id=context.membership.tenant_id,
            privileged=False,
        )
        return success(_agent_payload(agent))


class AgencyAgentPauseView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.update")
        agent = pause_agent().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            actor_tenant_id=context.membership.tenant_id,
            privileged=False,
        )
        return success(_agent_payload(agent))


class AgencyAgentCloneView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.create")
        raw_customer = request.data.get("customer_id") if request.data else None
        customer_id = (
            None
            if raw_customer in (None, "")
            else parse_uuid(raw_customer, field="customer_id")
        )
        agent = clone_agent().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            actor_tenant_id=context.membership.tenant_id,
            privileged=False,
            customer_id=customer_id,
        )
        return success(_agent_payload(agent), status=201)


class AgencyAgentResolvedView(CsrfAPIView):
    def get(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        agent = tenant_agents().get_agent(tenant_id, parse_uuid(agent_id, field="agent_id"))
        if agent is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return success(
            {
                "resolved": resolve_for_agent(agent, tenant_agents(), global_instructions()),
                "production_routable": False
                if agent.published_version is None
                else agent.status.value == "active",
            }
        )


class AgencyAgentRoutingView(CsrfAPIView):
    def get(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        try:
            assert_agent_routable(
                tenant_agents(),
                tenant_id=tenant_id,
                agent_id=parse_uuid(agent_id, field="agent_id"),
                production=True,
            )
        except DomainError as exc:
            if exc.code == "agent_not_routable":
                return success({"routable": False, "reason": exc.details.get("reason")})
            raise
        return success({"routable": True, "reason": None})


class AgencyAgentTestSessionView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.update")
        result = start_test_session().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            actor_tenant_id=context.membership.tenant_id,
            privileged=False,
            kind=str(request.data.get("kind") or "test"),
            query=str(request.data.get("query") or ""),
        )
        return success(result, status=201)


class AgencyTemplateCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        visible = []
        for row in templates().list(status=TemplateStatus.ACTIVE):
            if row.visibility is TemplateVisibility.INTERNAL:
                continue
            if row.visibility is TemplateVisibility.SELECTED:
                if tenant_id not in row.selected_tenant_ids:
                    continue
            visible.append(row)
        limit, offset = parse_page(
            request.query_params.get("limit"), request.query_params.get("offset")
        )
        rows, page = page_slice(visible, offset, limit)
        return success([_template_payload(row) for row in rows], page=page)


class AgencyInstructionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        raw_customer = request.query_params.get("customer_id")
        if raw_customer:
            customer_id = parse_uuid(raw_customer, field="customer_id")
            customer = customer_index().get(customer_id)
            if customer is None or customer.tenant_id != tenant_id:
                raise DomainError("not_found", "Resource not found.", http_status=404)
            row = tenant_agents().get_instruction(tenant_id, "customer", customer_id)
            return success(
                {
                    "scope": "customer",
                    "owner_id": str(customer_id),
                    "body": row.body if row else "",
                }
            )
        row = tenant_agents().get_instruction(tenant_id, "agency", tenant_id)
        return success({"scope": "agency", "body": row.body if row else ""})

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.update")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        raw_customer = request.data.get("customer_id")
        if raw_customer:
            customer_id = parse_uuid(raw_customer, field="customer_id")
            customer = customer_index().get(customer_id)
            if customer is None or customer.tenant_id != tenant_id:
                raise DomainError("not_found", "Resource not found.", http_status=404)
            return success(
                save_instruction().execute(
                    tenant_id=tenant_id,
                    scope="customer",
                    owner_id=customer_id,
                    body=str(request.data.get("body") or ""),
                    actor_tenant_id=tenant_id,
                    privileged=False,
                    actor_id=context.user.id,
                    actor_role=context.membership.role,
                    customer_id=customer_id,
                )
            )
        return success(
            save_instruction().execute(
                tenant_id=tenant_id,
                scope="agency",
                owner_id=tenant_id,
                body=str(request.data.get("body") or ""),
                actor_tenant_id=tenant_id,
                privileged=False,
                actor_id=context.user.id,
                actor_role=context.membership.role,
            )
        )


class AgencyKnowledgeView(CsrfAPIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        rows = [_knowledge_list_item(row) for row in tenant_agents().list_knowledge(tenant_id)]
        return success(rows)

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.update")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        scope = str(request.data.get("scope") or "agency")
        owner_raw = (
            request.data.get("owner_id") or request.data.get("customer_id") or str(tenant_id)
        )
        file_bytes, filename, content_type = _file_from_request(request)
        result = ingest_knowledge().execute(
            IngestKnowledgeCommand(
                tenant_id=tenant_id,
                scope=scope,
                owner_id=parse_uuid(owner_raw, field="owner_id"),
                title=str(request.data.get("title") or ""),
                body=str(request.data.get("body") or ""),
                kind=str(request.data.get("kind") or "text"),
                object_ref=str(request.data.get("object_ref") or ""),
                actor_tenant_id=tenant_id,
                filename=filename,
                content_type=content_type,
                file_bytes=file_bytes,
            )
        )
        return success(result, status=201)


class AgencyKnowledgeSourceView(CsrfAPIView):
    def get(self, request: Request, source_id: str) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        return success(
            source_impact(tenant_agents(), tenant_id, parse_uuid(source_id, field="source_id"))
        )

    def delete(self, request: Request, source_id: str) -> Response:
        context = require_agency_perm(request, "agent.update")
        result = delete_knowledge().execute(
            source_id=parse_uuid(source_id, field="source_id"),
            actor_tenant_id=context.membership.tenant_id,
            privileged=False,
            confirm=_confirm_delete(request),
            actor_id=context.user.id,
            actor_role=context.membership.role,
        )
        return success(result)


class AgencyKnowledgeAttachView(CsrfAPIView):
    def get(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        parsed = parse_uuid(agent_id, field="agent_id")
        agent = tenant_agents().get_agent(tenant_id, parsed)
        if agent is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        rows = []
        for row in tenant_agents().list_attachments(tenant_id, agent.agent_id):
            source = tenant_agents().get_knowledge(tenant_id, row.source_id)
            rows.append(
                {
                    "source_id": str(row.source_id),
                    "scope": row.scope,
                    "group_id": row.group_id,
                    "title": source.title if source else "",
                    "status": source.status if source else "",
                }
            )
        return success(rows)

    def post(self, request: Request, agent_id: str) -> Response:
        context = require_agency_perm(request, "agent.update")
        attach_knowledge().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            source_id=parse_uuid(request.data.get("source_id"), field="source_id"),
            actor_tenant_id=context.membership.tenant_id,
            privileged=False,
            global_group=bool(request.data.get("global") or False),
        )
        return success({"attached": True})


class AgencyKnowledgeDetachView(CsrfAPIView):
    def delete(self, request: Request, agent_id: str, source_id: str) -> Response:
        context = require_agency_perm(request, "agent.update")
        detach_knowledge().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            source_id=parse_uuid(source_id, field="source_id"),
            actor_tenant_id=context.membership.tenant_id,
            privileged=False,
        )
        return success({"detached": True})


class CustomerAgentDetailView(CsrfAPIView):
    def get(self, request: Request, agent_id: str) -> Response:
        context = require_customer_perm(request, "agent.view")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        agent = tenant_agents().get_agent(
            membership.tenant_id, parse_uuid(agent_id, field="agent_id")
        )
        if agent is None or agent.customer_id != membership.customer_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return success(_agent_payload(agent))

    def patch(self, request: Request, agent_id: str) -> Response:
        context = require_customer_perm(request, "agent.view")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        current = tenant_agents().get_agent(
            membership.tenant_id, parse_uuid(agent_id, field="agent_id")
        )
        if current is None or current.customer_id != membership.customer_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if not current.customer_can_edit:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        allowed = {
            key: request.data[key]
            for key in ("greeting", "instructions")
            if key in request.data
        }
        agent = configure_agent().execute(
            _configure_command(
                current.agent_id,
                allowed,
                tenant_id=membership.tenant_id,
                privileged=True,
            )
        )
        return success(_agent_payload(agent))


class CustomerKnowledgeView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_customer_perm(request, "knowledge.view")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        rows = [
            {
                "id": str(row.source_id),
                "title": row.title,
                "scope": row.scope,
                "status": row.status,
            }
            for row in tenant_agents().list_knowledge(membership.tenant_id, scope="customer")
            if row.owner_id == membership.customer_id
        ]
        return success(rows)
