"""TEN-006: financial / KYC / audit rows cannot be hard-deleted."""

from __future__ import annotations

import uuid

import pytest

from control_plane.audit.models import AuditEvent
from control_plane.billing.models import InvoiceIndex, PaymentProcessorEvent
from control_plane.commission.domain.types import LedgerKind
from control_plane.commission.models import LedgerEntry, Payout, PayoutProof
from control_plane.kyc.models import KycCase, KycProviderEvent
from control_plane.tenancy.models import Tenant
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7


def _expect_hard_delete(action) -> None:
    with pytest.raises(DomainError) as exc:
        action()
    assert exc.value.code in {"hard_delete_forbidden", "audit_immutable"}
    assert exc.value.http_status == 409


@pytest.mark.django_db
def test_audit_event_instance_and_queryset_delete_denied() -> None:
    row = AuditEvent.objects.create(
        action="login",
        entity_type="user",
        entity_id=str(new_uuid7()),
        severity="info",
    )
    _expect_hard_delete(row.delete)
    _expect_hard_delete(lambda: AuditEvent.objects.filter(pk=row.pk).delete())
    assert AuditEvent.objects.filter(pk=row.pk).exists()


@pytest.mark.django_db
def test_ledger_entry_hard_delete_denied() -> None:
    row = LedgerEntry.objects.create(
        tenant_id=new_uuid7(),
        kind=LedgerKind.COMMISSION_EARNED.value,
        amount_minor=1000,
        payment_id=new_uuid7(),
        commission_id=new_uuid7(),
    )
    _expect_hard_delete(row.delete)
    _expect_hard_delete(lambda: LedgerEntry.objects.filter(pk=row.pk).delete())
    assert LedgerEntry.objects.filter(pk=row.pk).exists()


@pytest.mark.django_db
def test_payout_and_proof_hard_delete_denied() -> None:
    payout = Payout.objects.create(
        tenant_id=new_uuid7(),
        amount_minor=5000,
        status="requested",
        requested_by_id=new_uuid7(),
    )
    proof = PayoutProof.objects.create(
        payout=payout,
        object_ref="proof/obj-1",
        content_type="image/png",
        checksum="abc",
        uploaded_by_id=new_uuid7(),
    )
    _expect_hard_delete(proof.delete)
    _expect_hard_delete(payout.delete)
    assert Payout.objects.filter(pk=payout.pk).exists()
    assert PayoutProof.objects.filter(pk=proof.pk).exists()


@pytest.mark.django_db
def test_invoice_and_payment_event_hard_delete_denied() -> None:
    invoice_id = new_uuid7()
    invoice = InvoiceIndex.objects.create(
        invoice_id=invoice_id,
        tenant_id=new_uuid7(),
        customer_id=new_uuid7(),
        status="open",
        total_minor=2500,
    )
    event = PaymentProcessorEvent.objects.create(
        processor="stripe",
        event_id=f"evt_{uuid.uuid4().hex}",
        invoice_id=invoice_id,
    )
    InvoiceIndex.objects.filter(invoice_id=invoice_id).update(status="paid")
    invoice.refresh_from_db()
    assert invoice.status == "paid"

    _expect_hard_delete(invoice.delete)
    _expect_hard_delete(event.delete)
    _expect_hard_delete(lambda: InvoiceIndex.objects.filter(pk=invoice_id).delete())
    assert InvoiceIndex.objects.filter(pk=invoice_id).exists()
    assert PaymentProcessorEvent.objects.filter(pk=event.pk).exists()


@pytest.mark.django_db
def test_kyc_case_and_provider_event_hard_delete_denied() -> None:
    tenant = Tenant.objects.create(display_name="Hard Delete KYC Tenant")
    case = KycCase.objects.create(tenant=tenant, status="pending_review")
    event = KycProviderEvent.objects.create(
        event_id=f"kyc_{uuid.uuid4().hex}",
        case=case,
        mapped_status="pending_review",
    )
    case.status = "approved"
    case.save(update_fields=["status", "updated_at"])

    _expect_hard_delete(event.delete)
    _expect_hard_delete(case.delete)
    _expect_hard_delete(lambda: KycCase.objects.filter(pk=case.pk).delete())
    assert KycCase.objects.filter(pk=case.pk).exists()
    assert KycProviderEvent.objects.filter(pk=event.pk).exists()
