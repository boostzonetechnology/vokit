from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.identity.api.auth import (
    parse_optional_uuid,
    parse_uuid,
    require_agency_perm,
    require_customer_perm,
    require_platform_perm,
    require_principal,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.notifications.application.service import DispatchCommand
from control_plane.notifications.domain.types import PreferenceScope
from control_plane.notifications.infrastructure.container import notifications
from control_plane.notifications.infrastructure.recipients import recipients_for_scope
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page


class PlatformTemplateCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "notification.view")
        return success(notifications().list_templates())

    def post(self, request: Request) -> Response:
        context = require_platform_perm(request, "notification.update")
        data = request.data if isinstance(request.data, dict) else {}
        payload = notifications().update_template(
            event_type=str(data.get("event_type") or ""),
            channel=str(data.get("channel") or ""),
            subject=str(data.get("subject") or ""),
            body=str(data.get("body") or ""),
        )
        record_audit().execute(
            RecordAuditCommand(
                action="settings.changed",
                entity_type="notification_template",
                entity_id=str(payload["event_type"]),
                actor_id=context.user.id,
                actor_role=context.membership.role,
                reason=str(data.get("reason") or "template update"),
                after_summary=str(payload["channel"]),
            )
        )
        return success(payload)


class PlatformDeliveryCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "notification.view")
        rows = notifications().list_deliveries()
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        sliced, page = page_slice(rows, offset, limit)
        return success(sliced, page=page)


class PlatformAnnouncementView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_platform_perm(request, "notification.create")
        data = request.data if isinstance(request.data, dict) else {}
        title = str(data.get("title") or "").strip()
        body = str(data.get("body") or "").strip()
        if not title or not body:
            raise DomainError("validation_error", "title and body are required.")
        tenant_id = parse_optional_uuid(data.get("agency_id"), field="agency_id")
        customer_id = parse_optional_uuid(data.get("customer_id"), field="customer_id")
        if customer_id is not None:
            recipients = recipients_for_scope(customer_id=customer_id)
        elif tenant_id is not None:
            recipients = recipients_for_scope(tenant_id=tenant_id)
        else:
            recipients = recipients_for_scope(platform=True)
        sent = notifications().dispatch(
            DispatchCommand(
                event_type="announcement.platform",
                recipients=tuple(recipients),
                variables={"title": title, "body": body},
                tenant_id=tenant_id,
                customer_id=customer_id,
            )
        )
        record_audit().execute(
            RecordAuditCommand(
                action="settings.changed",
                entity_type="announcement",
                entity_id="announcement.platform",
                actor_id=context.user.id,
                actor_role=context.membership.role,
                tenant_id=tenant_id,
                customer_id=customer_id,
                reason=str(data.get("reason") or "announcement"),
                after_summary=title[:255],
            )
        )
        return success({"sent": sent}, status=201)


class InboxView(CsrfAPIView):
    principal_type: PrincipalType = PrincipalType.PLATFORM

    def get(self, request: Request) -> Response:
        context = require_principal(request, self.principal_type)
        return success(notifications().inbox_for(context.user.id))


class InboxReadView(CsrfAPIView):
    principal_type: PrincipalType = PrincipalType.PLATFORM

    def post(self, request: Request, notification_id: str) -> Response:
        context = require_principal(request, self.principal_type)
        return success(
            notifications().mark_read(
                parse_uuid(notification_id, field="notification_id"),
                context.user.id,
            )
        )


class AgencyPreferenceView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "notice.update")
        return success(
            notifications().list_preferences(
                scope=PreferenceScope.AGENCY,
                user_id=None,
                tenant_id=context.membership.tenant_id,
                customer_id=None,
            )
        )

    def put(self, request: Request) -> Response:
        context = require_agency_perm(request, "notice.update")
        data = request.data if isinstance(request.data, dict) else {}
        items = data.get("preferences")
        if type(items) is not list:
            raise DomainError("validation_error", "preferences must be a list.")
        return success(
            notifications().set_preferences(
                scope=PreferenceScope.AGENCY,
                user_id=None,
                tenant_id=context.membership.tenant_id,
                customer_id=None,
                items=items,
            )
        )


class CustomerPreferenceView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_customer_perm(request, "notice.update")
        return success(
            notifications().list_preferences(
                scope=PreferenceScope.CUSTOMER,
                user_id=None,
                tenant_id=context.membership.tenant_id,
                customer_id=context.membership.customer_id,
            )
        )

    def put(self, request: Request) -> Response:
        context = require_customer_perm(request, "notice.update")
        data = request.data if isinstance(request.data, dict) else {}
        items = data.get("preferences")
        if type(items) is not list:
            raise DomainError("validation_error", "preferences must be a list.")
        return success(
            notifications().set_preferences(
                scope=PreferenceScope.CUSTOMER,
                user_id=None,
                tenant_id=context.membership.tenant_id,
                customer_id=context.membership.customer_id,
                items=items,
            )
        )
