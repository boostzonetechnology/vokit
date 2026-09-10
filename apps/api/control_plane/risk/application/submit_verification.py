from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.customers.domain.policies import customer_not_found
from control_plane.risk.application.ports import (
    RiskCaseRecord,
    RiskCaseRepository,
    VerificationRecord,
    VerificationRepository,
)
from control_plane.risk.domain.policies import (
    CardMaskAssessment,
    assert_card_mask,
    assert_commercially_open,
    assert_no_sensitive_card_payload,
)
from control_plane.risk.domain.types import RiskStatus, VerificationStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.risk")


@dataclass(frozen=True, slots=True)
class SubmitVerificationCommand:
    customer_id: uuid.UUID
    actor_customer_id: uuid.UUID | None
    privileged: bool
    payload: dict
    id_object_ref: str
    id_content_type: str
    id_checksum: str
    card_object_ref: str
    card_checksum: str
    card_last4: str
    visible_digit_count: int
    cvv_visible: bool
    full_pan_present: bool


class SubmitVerification:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        cases: RiskCaseRepository,
        verifications: VerificationRepository,
        clock: Clock,
    ) -> None:
        self._customers = customers
        self._cases = cases
        self._verifications = verifications
        self._clock = clock

    def execute(self, command: SubmitVerificationCommand) -> VerificationRecord:
        assert_no_sensitive_card_payload(command.payload)
        customer = self._customers.get(command.customer_id)
        if customer is None:
            raise customer_not_found()
        if not command.privileged:
            if (
                command.actor_customer_id is None
                or command.actor_customer_id != customer.id
            ):
                raise customer_not_found()
        case = self._cases.get_for_customer(customer.id)
        assert_commercially_open(
            case.status if case is not None else None,
            permanently_banned=bool(case.permanently_banned) if case is not None else False,
        )
        assert_card_mask(
            CardMaskAssessment(
                last4=command.card_last4,
                visible_digit_count=command.visible_digit_count,
                cvv_visible=command.cvv_visible,
                full_pan_present=command.full_pan_present,
            )
        )
        for required in (
            command.id_object_ref,
            command.id_checksum,
            command.card_object_ref,
            command.card_checksum,
        ):
            if not required.strip():
                raise DomainError("validation_error", "Verification object refs are required.")
        now = self._clock.now()
        if case is None:
            case = RiskCaseRecord(
                id=new_uuid7(),
                tenant_id=customer.tenant_id,
                customer_id=customer.id,
                status=RiskStatus.VERIFICATION_SUBMITTED,
                last_invoice_id=None,
                last_payment_id=None,
                last_event_id="",
                note="verification",
                permanently_banned=False,
                created_at=now,
                updated_at=now,
            )
        else:
            case = RiskCaseRecord(
                id=case.id,
                tenant_id=case.tenant_id,
                customer_id=case.customer_id,
                status=RiskStatus.VERIFICATION_SUBMITTED,
                last_invoice_id=case.last_invoice_id,
                last_payment_id=case.last_payment_id,
                last_event_id=case.last_event_id,
                note=case.note or "verification",
                permanently_banned=case.permanently_banned,
                created_at=case.created_at,
                updated_at=now,
            )
        record = VerificationRecord(
            id=new_uuid7(),
            case_id=case.id,
            status=VerificationStatus.SUBMITTED,
            id_object_ref=command.id_object_ref.strip()[:128],
            id_checksum=command.id_checksum.strip()[:128],
            card_object_ref=command.card_object_ref.strip()[:128],
            card_checksum=command.card_checksum.strip()[:128],
            card_last4=command.card_last4.strip(),
        )
        self._cases.upsert(case)
        self._verifications.create(record)
        log_event(
            logger,
            "risk.verification.submitted",
            outcome="success",
            tenant_id=str(customer.tenant_id),
            customer_id=str(customer.id),
            case_id=str(case.id),
        )
        return record
