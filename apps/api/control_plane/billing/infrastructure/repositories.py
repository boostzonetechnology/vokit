from __future__ import annotations

import uuid

from django.conf import settings
from django.db import IntegrityError

from control_plane.billing.application.ports import (
    BillingSettingsRecord,
    IdempotencyRecord,
    InvoiceIndexRecord,
    PlanRecord,
    PlanVersionRecord,
    ProcessorEventRecord,
)
from control_plane.billing.domain.types import InvoiceStatus, PlanStatus, ProcessorEventStatus
from control_plane.billing.models import (
    BillingIdempotencyKey,
    BillingSettings,
    InvoiceIndex,
    PaymentProcessorEvent,
    Plan,
    PlanVersion,
)
from shared_kernel.errors import DomainError
from shared_kernel.money import Money


def _plan(row: Plan) -> PlanRecord:
    return PlanRecord(
        id=row.id,
        name=row.name,
        status=PlanStatus(row.status),
        created_at=row.created_at,
    )


def _version(row: PlanVersion) -> PlanVersionRecord:
    return PlanVersionRecord(
        id=row.id,
        plan_id=row.plan_id,
        version=row.version,
        price=Money(int(row.price_minor), row.currency),
        included_minutes=int(row.included_minutes),
        allow_topups=bool(row.allow_topups),
        topup_minutes=int(row.topup_minutes),
        topup_price=Money(int(row.topup_price_minor), row.currency),
        overage_enabled=bool(row.overage_enabled),
        overage_price_per_minute=Money(int(row.overage_price_per_minute_minor), row.currency),
        grace_seconds=int(row.grace_seconds),
        used_at=row.used_at,
        created_at=row.created_at,
    )


def _index(row: InvoiceIndex) -> InvoiceIndexRecord:
    return InvoiceIndexRecord(
        invoice_id=row.invoice_id,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        status=InvoiceStatus(row.status),
        total=Money(int(row.total_minor), row.currency),
        created_at=row.created_at,
        paid_at=row.paid_at,
    )


class DjangoPlanRepository:
    def create(self, record: PlanRecord) -> None:
        Plan.objects.create(id=record.id, name=record.name, status=record.status.value)

    def get(self, plan_id: uuid.UUID) -> PlanRecord | None:
        row = Plan.objects.filter(id=plan_id).first()
        return _plan(row) if row else None

    def list(self, *, status: PlanStatus | None = None) -> list[PlanRecord]:
        rows = Plan.objects.order_by("created_at")
        if status is not None:
            rows = rows.filter(status=status.value)
        return [_plan(row) for row in rows]

    def update(self, record: PlanRecord) -> None:
        Plan.objects.filter(id=record.id).update(name=record.name, status=record.status.value)


class DjangoPlanVersionRepository:
    def create(self, record: PlanVersionRecord) -> None:
        PlanVersion.objects.create(
            id=record.id,
            plan_id=record.plan_id,
            version=record.version,
            price_minor=record.price.minor_units,
            currency=record.price.currency,
            included_minutes=record.included_minutes,
            allow_topups=record.allow_topups,
            topup_minutes=record.topup_minutes,
            topup_price_minor=record.topup_price.minor_units,
            overage_enabled=record.overage_enabled,
            overage_price_per_minute_minor=record.overage_price_per_minute.minor_units,
            grace_seconds=record.grace_seconds,
            used_at=record.used_at,
        )

    def get(self, version_id: uuid.UUID) -> PlanVersionRecord | None:
        row = PlanVersion.objects.filter(id=version_id).first()
        return _version(row) if row else None

    def list_for_plan(self, plan_id: uuid.UUID) -> list[PlanVersionRecord]:
        rows = PlanVersion.objects.filter(plan_id=plan_id).order_by("version")
        return [_version(row) for row in rows]

    def update(self, record: PlanVersionRecord) -> None:
        PlanVersion.objects.filter(id=record.id).update(
            price_minor=record.price.minor_units,
            currency=record.price.currency,
            included_minutes=record.included_minutes,
            allow_topups=record.allow_topups,
            topup_minutes=record.topup_minutes,
            topup_price_minor=record.topup_price.minor_units,
            overage_enabled=record.overage_enabled,
            overage_price_per_minute_minor=record.overage_price_per_minute.minor_units,
            grace_seconds=record.grace_seconds,
            used_at=record.used_at,
        )

    def next_version(self, plan_id: uuid.UUID) -> int:
        latest = PlanVersion.objects.filter(plan_id=plan_id).order_by("-version").first()
        return (latest.version + 1) if latest else 1


class DjangoInvoiceIndexRepository:
    def create(self, record: InvoiceIndexRecord) -> None:
        InvoiceIndex.objects.create(
            invoice_id=record.invoice_id,
            tenant_id=record.tenant_id,
            customer_id=record.customer_id,
            status=record.status.value,
            total_minor=record.total.minor_units,
            currency=record.total.currency,
            paid_at=record.paid_at,
        )

    def get(self, invoice_id: uuid.UUID) -> InvoiceIndexRecord | None:
        row = InvoiceIndex.objects.filter(invoice_id=invoice_id).first()
        return _index(row) if row else None

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        status: InvoiceStatus | None = None,
    ) -> list[InvoiceIndexRecord]:
        rows = InvoiceIndex.objects.order_by("created_at")
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if customer_id is not None:
            rows = rows.filter(customer_id=customer_id)
        if status is not None:
            rows = rows.filter(status=status.value)
        return [_index(row) for row in rows]

    def update(self, record: InvoiceIndexRecord) -> None:
        InvoiceIndex.objects.filter(invoice_id=record.invoice_id).update(
            status=record.status.value,
            total_minor=record.total.minor_units,
            currency=record.total.currency,
            paid_at=record.paid_at,
        )


class DjangoProcessorEventRepository:
    def get(self, processor: str, event_id: str) -> ProcessorEventRecord | None:
        row = PaymentProcessorEvent.objects.filter(
            processor=processor, event_id=event_id
        ).first()
        if row is None:
            return None
        return ProcessorEventRecord(
            processor=row.processor,
            event_id=row.event_id,
            invoice_id=row.invoice_id,
            status=ProcessorEventStatus(row.status),
        )

    def create(self, record: ProcessorEventRecord) -> None:
        try:
            PaymentProcessorEvent.objects.create(
                processor=record.processor,
                event_id=record.event_id,
                invoice_id=record.invoice_id,
                status=record.status.value,
            )
        except IntegrityError as exc:
            raise DomainError(
                "processor_event_duplicate",
                "Payment event was already received.",
            ) from exc


class DjangoBillingSettingsRepository:
    def get(self) -> BillingSettingsRecord:
        row = BillingSettings.objects.first()
        if row is None:
            row = BillingSettings.objects.create(
                stripe_webhook_secret_ref=getattr(
                    settings, "BILLING_STRIPE_WEBHOOK_SECRET_REF", "STRIPE_WEBHOOK_SECRET"
                ),
                braintree_webhook_secret_ref=getattr(
                    settings,
                    "BILLING_BRAINTREE_WEBHOOK_SECRET_REF",
                    "BRAINTREE_WEBHOOK_SECRET",
                ),
            )
        return BillingSettingsRecord(
            stripe_webhook_secret_ref=row.stripe_webhook_secret_ref,
            braintree_webhook_secret_ref=row.braintree_webhook_secret_ref,
        )


class DjangoBillingIdempotencyRepository:
    def get(self, actor_id: uuid.UUID, key: str) -> IdempotencyRecord | None:
        row = BillingIdempotencyKey.objects.filter(actor_id=actor_id, key=key).first()
        if row is None:
            return None
        return IdempotencyRecord(
            actor_id=row.actor_id,
            key=row.key,
            kind=row.kind,
            resource_id=row.resource_id,
        )

    def create(self, record: IdempotencyRecord) -> None:
        try:
            BillingIdempotencyKey.objects.create(
                actor_id=record.actor_id,
                key=record.key,
                kind=record.kind,
                resource_id=record.resource_id,
            )
        except IntegrityError:
            return
