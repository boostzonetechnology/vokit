from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.agents.application.builder import (
    ConfigureAgentCommand,
    assert_agent_routable,
)
from control_plane.agents.application.knowledge import IngestKnowledgeCommand
from control_plane.agents.application.resolve import resolve_for_agent
from control_plane.agents.application.templates import CreateTemplateCommand
from control_plane.agents.domain.types import TemplateStatus, TemplateVisibility
from control_plane.agents.infrastructure.container import (
    agent_index,
    attach_knowledge,
    clone_agent,
    configure_agent,
    create_template,
    global_instructions,
    global_knowledge,
    ingest_knowledge,
    install_template,
    pause_agent,
    publish_agent,
    save_instruction,
    start_test_session,
    template_versions,
    templates,
)
from control_plane.identity.api.auth import (
    parse_optional_uuid,
    parse_uuid,
    require_agency_perm,
    require_customer_perm,
    require_platform_perm,
)
from control_plane.identity.api.views import CsrfAPIView
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
        "template_id": str(row.template_id) if row.template_id else None,
        "customer_can_edit": row.customer_can_edit,
        "business_hours": list(row.business_hours),
        "voicemail_greeting": row.voicemail_greeting,
        "outbound_voicemail_message": row.outbound_voicemail_message,
        "default_transfer_id": (
            str(row.default_transfer_id) if row.default_transfer_id else None
        ),
        "production_routable": bool(
            row.status.value == "active" and row.published_version is not None
        ),
    }


def _index_payload(row) -> dict[str, object]:
    return {
        "id": str(row.id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "display_name": row.display_name,
        "status": row.status.value,
        "agent_type": row.agent_type,
        "published_version": row.published_version,
        "production_routable": bool(
            row.status.value == "active" and row.published_version is not None
        ),
    }


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
    )


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
        rows, page = page_slice(
            agent_index().list(
                tenant_id=parse_optional_uuid(
                    request.query_params.get("agency_id"), field="agency_id"
                ),
                customer_id=parse_optional_uuid(
                    request.query_params.get("customer_id"), field="customer_id"
                ),
            ),
            offset,
            limit,
        )
        return success([_index_payload(row) for row in rows], page=page)

    def post(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        agent = create_agent().execute(
            CreateAgentCommand(
                customer_id=parse_uuid(request.data.get("customer_id"), field="customer_id"),
                display_name=str(request.data.get("display_name") or ""),
                actor_tenant_id=None,
                privileged=True,
            )
        )
        return success(_agent_payload(agent), status=201)


class PlatformAgentPublishView(CsrfAPIView):
    def post(self, request: Request, agent_id: str) -> Response:
        require_platform_perm(request, "agent.view")
        agent = publish_agent().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            actor_tenant_id=None,
            privileged=True,
        )
        return success(_agent_payload(agent))


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
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        agency_id = parse_optional_uuid(
            request.query_params.get("agency_id"), field="agency_id"
        )
        if agency_id is not None:
            rows = [
                {
                    "id": str(row.source_id),
                    "title": row.title,
                    "scope": row.scope,
                    "status": row.status,
                    "group_id": row.group_id,
                    "agency_id": str(agency_id),
                }
                for row in tenant_agents().list_knowledge(agency_id)
            ]
            return success(rows)
        rows = [
            {"id": str(item[0]), "title": item[1], "scope": "global"}
            for item in global_knowledge().list()
        ]
        return success(rows)

    def post(self, request: Request) -> Response:
        require_platform_perm(request, "agent.view")
        from uuid import UUID

        result = ingest_knowledge().execute(
            IngestKnowledgeCommand(
                tenant_id=UUID("00000000-0000-7000-8000-000000000009"),
                scope="global",
                owner_id=UUID("00000000-0000-7000-8000-000000000009"),
                title=str(request.data.get("title") or ""),
                body=str(request.data.get("body") or ""),
                kind=str(request.data.get("kind") or "text"),
                privileged=True,
            )
        )
        return success(result, status=201)


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
        agent = clone_agent().execute(
            agent_id=parse_uuid(agent_id, field="agent_id"),
            actor_tenant_id=context.membership.tenant_id,
            privileged=False,
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
        row = tenant_agents().get_instruction(tenant_id, "agency", tenant_id)
        return success({"scope": "agency", "body": row.body if row else ""})

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.update")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        return success(
            save_instruction().execute(
                tenant_id=tenant_id,
                scope="agency",
                owner_id=tenant_id,
                body=str(request.data.get("body") or ""),
                actor_tenant_id=tenant_id,
                privileged=False,
            )
        )


class AgencyKnowledgeView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        rows = [
            {
                "id": str(row.source_id),
                "title": row.title,
                "scope": row.scope,
                "status": row.status,
                "group_id": row.group_id,
            }
            for row in tenant_agents().list_knowledge(tenant_id)
        ]
        return success(rows)

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "agent.update")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        scope = str(request.data.get("scope") or "agency")
        owner_id = parse_uuid(
            request.data.get("owner_id") or str(tenant_id), field="owner_id"
        )
        result = ingest_knowledge().execute(
            IngestKnowledgeCommand(
                tenant_id=tenant_id,
                scope=scope,
                owner_id=owner_id,
                title=str(request.data.get("title") or ""),
                body=str(request.data.get("body") or ""),
                kind=str(request.data.get("kind") or "text"),
                actor_tenant_id=tenant_id,
            )
        )
        return success(result, status=201)


class AgencyKnowledgeAttachView(CsrfAPIView):
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
