from __future__ import annotations

from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.identity.domain.types import PrincipalType
from control_plane.notifications.application.service import DispatchCommand
from control_plane.notifications.infrastructure.container import notifications
from control_plane.notifications.infrastructure.recipients import (
    invitation_recipient,
    recipients_for_scope,
)


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
    notifications().dispatch(
        DispatchCommand(
            event_type=event,
            recipients=(recipient,),
            variables={"email": email, "role": role, "token": token},
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
    }
    event = mapping.get(status)
    if event is None:
        return
    recipients = recipients_for_scope(tenant_id=tenant_id)
    if not recipients:
        return
    notifications().dispatch(
        DispatchCommand(
            event_type=event,
            recipients=tuple(recipients),
            variables={"agency_id": str(tenant_id), "status": status},
            tenant_id=tenant_id,
        )
    )
