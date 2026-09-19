from __future__ import annotations

import logging

from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.identity.domain.types import PrincipalType
from control_plane.notifications.application.ports import Recipient
from control_plane.notifications.application.service import DispatchCommand
from control_plane.notifications.infrastructure.container import notifications
from control_plane.notifications.infrastructure.invite_links import invitation_accept_url
from control_plane.notifications.infrastructure.recipients import (
    invitation_recipient,
    recipients_for_scope,
)
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.notifications")


def deliver_invitation(
    *,
    email: str,
    role: str,
    principal_type: PrincipalType,
    tenant_id,
    customer_id,
    token: str,
    actor_id,
    actor_role: str,
) -> None:
    event = {
        PrincipalType.PLATFORM: "invitation.platform",
        PrincipalType.AGENCY: "invitation.agency",
        PrincipalType.CUSTOMER: "invitation.customer",
    }[principal_type]
    recipient = invitation_recipient(
        email=email, tenant_id=tenant_id, customer_id=customer_id
    )
    accept_url = invitation_accept_url(principal_type=principal_type, token=token)
    notifications().dispatch(
        DispatchCommand(
            event_type=event,
            recipients=(recipient,),
            variables={
                "email": email,
                "role": role,
                "token": token,
                "accept_url": accept_url,
            },
            tenant_id=tenant_id,
            customer_id=customer_id,
        )
    )
    record_audit().execute(
        RecordAuditCommand(
            action="role.invited",
            entity_type="invitation",
            entity_id=email,
            actor_id=actor_id,
            actor_role=actor_role,
            tenant_id=tenant_id,
            customer_id=customer_id,
            after_summary=role,
            payload={"principal_type": principal_type.value, "role": role},
        )
    )


def kyc_notify(*, tenant_id, status: str) -> None:
    mapping = {
        "submitted": "kyc.submitted",
        "verified": "kyc.approved",
        "rejected": "kyc.rejected",
        "more_information_required": "kyc.more_info",
        "suspended": "agency.suspended",
        "restricted": "agency.suspended",
    }
    event = mapping.get(status)
    if event is None:
        return
    recipients = recipients_for_scope(tenant_id=tenant_id)
    if not recipients:
        return
    variables = {"agency_id": str(tenant_id)}
    if event != "agency.suspended":
        variables["status"] = status
    notifications().dispatch(
        DispatchCommand(
            event_type=event,
            recipients=tuple(recipients),
            variables=variables,
            tenant_id=tenant_id,
        )
    )


def billing_notify(
    *,
    event_type: str,
    recipients: list[Recipient] | tuple[Recipient, ...],
    variables: dict[str, str],
    tenant_id=None,
    customer_id=None,
) -> None:
    unique: list[Recipient] = []
    seen: set[tuple[object, str]] = set()
    for row in recipients:
        key = (row.user_id, row.email)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    if not unique:
        return
    try:
        notifications().dispatch(
            DispatchCommand(
                event_type=event_type,
                recipients=tuple(unique),
                variables=variables,
                tenant_id=tenant_id,
                customer_id=customer_id,
            )
        )
    except Exception:
        log_event(
            logger,
            "notification.dispatched",
            outcome="error",
            event_type=event_type,
        )
