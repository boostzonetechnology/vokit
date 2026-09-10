from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from control_plane.billing.application.add_plan_version import (
    AddPlanVersionCommand,
    UpdatePlanVersionCommand,
)
from control_plane.billing.application.assign_subscription import AssignSubscriptionCommand
from control_plane.billing.application.create_plan import CreatePlanCommand
from control_plane.billing.application.create_topup import CreateTopUpCommand
from control_plane.billing.application.pay_invoice import PayInvoiceCommand
from control_plane.billing.domain.lots import LotBalance, remaining_minutes
from control_plane.billing.domain.types import DRAIN_ORDER, InvoiceStatus, PlanStatus
from control_plane.billing.infrastructure.container import (
    add_plan_version,
    archive_plan,
    assign_subscription,
    billing_settings,
    create_plan,
    create_topup,
    invoice_index,
    pay_invoice,
    payment_processor,
    plan_versions,
    plans,
    settle_payment,
    tenant_billing,
    update_plan_version,
)
from control_plane.identity.api.auth import (
    parse_optional_uuid,
    parse_uuid,
    require_principal,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page
from tenant.billing.domain import InvoiceRecord


def _require_platform_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.PLATFORM)
    if permission not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _require_agency_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.AGENCY)
    if permission not in context.permissions or context.membership.tenant_id is None:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _require_customer_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.CUSTOMER)
    membership = context.membership
    if (
        permission not in context.permissions
        or membership.tenant_id is None
        or membership.customer_id is None
    ):
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _int_field(data: dict, name: str, default: int | None = None) -> int:
    raw = data.get(name, default)
    if raw is None:
        raise DomainError("validation_error", f"{name} is required.")
    if type(raw) is bool or type(raw) is float:
        raise DomainError("validation_error", f"{name} must be an integer.")
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise DomainError("validation_error", f"{name} must be an integer.") from exc


def _bool_field(data: dict, name: str, default: bool = False) -> bool:
    raw = data.get(name, default)
    if type(raw) is not bool:
        raise DomainError("validation_error", f"{name} must be a boolean.")
    return raw


def _plan_terms(data: dict) -> dict:
    return {
        "price_minor": _int_field(data, "price_minor"),
        "included_minutes": _int_field(data, "included_minutes"),
        "allow_topups": _bool_field(data, "allow_topups"),
        "topup_minutes": _int_field(data, "topup_minutes", 0),
        "topup_price_minor": _int_field(data, "topup_price_minor", 0),
        "overage_enabled": _bool_field(data, "overage_enabled"),
        "overage_price_per_minute_minor": _int_field(
            data, "overage_price_per_minute_minor", 0
        ),
        "grace_seconds": _int_field(data, "grace_seconds", 0),
    }


def _version_payload(row) -> dict[str, object]:
    return {
        "id": str(row.id),
        "plan_id": str(row.plan_id),
        "version": row.version,
        "price_minor": row.price.minor_units,
        "currency": row.price.currency,
        "included_minutes": row.included_minutes,
        "allow_topups": row.allow_topups,
        "topup_minutes": row.topup_minutes,
        "topup_price_minor": row.topup_price.minor_units,
        "overage_enabled": row.overage_enabled,
        "overage_price_per_minute_minor": row.overage_price_per_minute.minor_units,
        "grace_seconds": row.grace_seconds,
        "used": row.used_at is not None,
    }


def _plan_payload(row) -> dict[str, object]:
    versions = [_version_payload(item) for item in plan_versions().list_for_plan(row.id)]
    return {
        "id": str(row.id),
        "name": row.name,
        "status": row.status.value,
        "versions": versions,
    }


def _invoice_payload(row: InvoiceRecord) -> dict[str, object]:
    return {
        "id": str(row.invoice_id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "subscription_id": str(row.subscription_id) if row.subscription_id else None,
        "status": row.status.value,
        "currency": row.currency,
        "total_minor": row.total_minor,
        "lines": [
            {
                "id": str(line.line_id),
                "kind": line.kind.value,
                "description": line.description,
                "amount_minor": line.amount_minor,
                "currency": line.currency,
                "minutes": line.minutes,
                "commissionable": line.commissionable,
            }
            for line in row.lines
        ],
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
    }


def _index_payload(row) -> dict[str, object]:
    return {
        "id": str(row.invoice_id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "status": row.status.value,
        "currency": row.total.currency,
        "total_minor": row.total.minor_units,
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
    }


class PlatformPlanCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "plans.manage")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows, page = page_slice(plans().list(), offset, limit)
        return success([_plan_payload(row) for row in rows], page=page)

    def post(self, request: Request) -> Response:
        _require_platform_perm(request, "plans.manage")
        plan, _version = create_plan().execute(
            CreatePlanCommand(name=str(request.data.get("name") or ""), **_plan_terms(request.data))
        )
        return success(_plan_payload(plan), status=201)


class PlatformPlanVersionView(CsrfAPIView):
    def post(self, request: Request, plan_id: str) -> Response:
        _require_platform_perm(request, "plans.manage")
        version = add_plan_version().execute(
            AddPlanVersionCommand(
                plan_id=parse_uuid(plan_id, field="plan_id"),
                **_plan_terms(request.data),
            )
        )
        return success(_version_payload(version), status=201)


class PlatformPlanVersionDetailView(CsrfAPIView):
    def patch(self, request: Request, version_id: str) -> Response:
        _require_platform_perm(request, "plans.manage")
        version = update_plan_version().execute(
            UpdatePlanVersionCommand(
                version_id=parse_uuid(version_id, field="version_id"),
                **_plan_terms(request.data),
            )
        )
        return success(_version_payload(version))


class PlatformPlanArchiveView(CsrfAPIView):
    def post(self, request: Request, plan_id: str) -> Response:
        _require_platform_perm(request, "plans.manage")
        plan = archive_plan().execute(parse_uuid(plan_id, field="plan_id"))
        return success(_plan_payload(plan))


class PlatformCustomerSubscriptionView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        _require_platform_perm(request, "customers.create")
        invoice = assign_subscription().execute(
            AssignSubscriptionCommand(
                customer_id=parse_uuid(customer_id, field="customer_id"),
                plan_version_id=parse_uuid(
                    request.data.get("plan_version_id"), field="plan_version_id"
                ),
                actor_tenant_id=None,
                privileged=True,
            )
        )
        return success(_invoice_payload(invoice), status=201)


class PlatformInvoiceCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "billing.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        status_raw = str(request.query_params.get("status") or "").strip()
        try:
            status = InvoiceStatus(status_raw) if status_raw else None
        except ValueError as exc:
            raise DomainError("validation_error", "status is invalid.") from exc
        rows = invoice_index().list(
            tenant_id=parse_optional_uuid(request.query_params.get("agency_id"), field="agency_id"),
            customer_id=parse_optional_uuid(
                request.query_params.get("customer_id"), field="customer_id"
            ),
            status=status,
        )
        sliced, page = page_slice(rows, offset, limit)
        return success([_index_payload(row) for row in sliced], page=page)


class PlatformPaymentCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "billing.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        invoice_id = parse_optional_uuid(
            request.query_params.get("invoice_id"), field="invoice_id"
        )
        indexed = invoice_index().list()
        payments = []
        for row in indexed:
            if invoice_id is not None and row.invoice_id != invoice_id:
                continue
            for payment in tenant_billing().list_payments(row.tenant_id, row.invoice_id):
                payments.append(
                    {
                        "id": str(payment.payment_id),
                        "invoice_id": str(payment.invoice_id),
                        "agency_id": str(payment.tenant_id),
                        "customer_id": str(payment.customer_id),
                        "processor": payment.processor,
                        "amount_minor": payment.amount_minor,
                        "currency": payment.currency,
                        "status": payment.status.value,
                    }
                )
        sliced, page = page_slice(payments, offset, limit)
        return success(sliced, page=page)


class PlatformDisputeCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        from control_plane.risk.infrastructure.container import risk_events

        _require_platform_perm(request, "billing.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows = [
            {
                "processor": row.processor,
                "event_id": row.event_id,
                "customer_id": str(row.customer_id) if row.customer_id else None,
                "kind": row.kind,
                "status": row.status,
            }
            for row in risk_events().list(kind="chargeback")
        ]
        sliced, page = page_slice(rows, offset, limit)
        return success(sliced, page=page)


class AgencyPlanCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_agency_perm(request, "customers.manage")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows, page = page_slice(plans().list(status=PlanStatus.ACTIVE), offset, limit)
        return success([_plan_payload(row) for row in rows], page=page)


class AgencyCustomerSubscriptionView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        context = _require_agency_perm(request, "customers.manage")
        invoice = assign_subscription().execute(
            AssignSubscriptionCommand(
                customer_id=parse_uuid(customer_id, field="customer_id"),
                plan_version_id=parse_uuid(
                    request.data.get("plan_version_id"), field="plan_version_id"
                ),
                actor_tenant_id=context.membership.tenant_id,
                privileged=False,
            )
        )
        return success(_invoice_payload(invoice), status=201)


class AgencyCustomerInvoiceCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = _require_agency_perm(request, "customers.manage")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        customer_id = parse_optional_uuid(
            request.query_params.get("customer_id"), field="customer_id"
        )
        rows = tenant_billing().list_invoices(tenant_id, customer_id)
        sliced, page = page_slice(rows, offset, limit)
        return success([_invoice_payload(row) for row in sliced], page=page)


class CustomerInvoiceCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = _require_customer_perm(request, "billing.pay")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows = tenant_billing().list_invoices(membership.tenant_id, membership.customer_id)
        sliced, page = page_slice(rows, offset, limit)
        return success([_invoice_payload(row) for row in sliced], page=page)


class CustomerInvoicePayView(CsrfAPIView):
    def post(self, request: Request, invoice_id: str) -> Response:
        context = _require_customer_perm(request, "billing.pay")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        intent = pay_invoice().execute(
            PayInvoiceCommand(
                tenant_id=membership.tenant_id,
                customer_id=membership.customer_id,
                invoice_id=parse_uuid(invoice_id, field="invoice_id"),
                actor_id=context.user.id,
                idempotency_key=str(request.headers.get("Idempotency-Key") or ""),
                processor=str(request.data.get("processor") or "stripe"),
            )
        )
        return success(
            {
                "invoice_id": str(intent.invoice.invoice_id),
                "processor": intent.processor,
                "amount_minor": intent.invoice.total_minor,
                "currency": intent.invoice.currency,
                "client_reference": intent.client_reference,
                "status": "awaiting_webhook",
            }
        )


class CustomerTopUpView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = _require_customer_perm(request, "billing.pay")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        invoice = create_topup().execute(
            CreateTopUpCommand(
                tenant_id=membership.tenant_id,
                customer_id=membership.customer_id,
                actor_id=context.user.id,
                idempotency_key=str(request.headers.get("Idempotency-Key") or ""),
            )
        )
        return success(_invoice_payload(invoice), status=201)


class CustomerUsageView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = _require_customer_perm(request, "billing.pay")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        lots = tenant_billing().list_lots(membership.tenant_id, membership.customer_id)
        subscription = tenant_billing().get_active_subscription(
            membership.tenant_id, membership.customer_id
        )
        version = plan_versions().get(subscription.plan_version_id) if subscription else None
        balances = tuple(
            LotBalance(
                lot_id=str(lot.lot_id),
                kind=lot.kind,
                remaining_minutes=lot.remaining_minutes,
            )
            for lot in lots
        )
        return success(
            {
                "remaining_minutes": remaining_minutes(balances),
                "drain_order": [kind.value for kind in DRAIN_ORDER],
                "overage_enabled": bool(version.overage_enabled) if version else False,
                "grace_seconds": int(version.grace_seconds) if version else 0,
                "lots": [
                    {
                        "id": str(lot.lot_id),
                        "kind": lot.kind.value,
                        "granted_minutes": lot.granted_minutes,
                        "remaining_minutes": lot.remaining_minutes,
                    }
                    for lot in lots
                ],
            }
        )


class CustomerPaymentMethodCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_customer_perm(request, "billing.pay")
        return success([], page={"next": None, "limit": 50, "offset": 0})


class PaymentWebhookView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request: Request, processor: str) -> Response:
        settings_row = billing_settings().get()
        if processor == "stripe":
            secret_ref = settings_row.stripe_webhook_secret_ref
        elif processor == "braintree":
            secret_ref = settings_row.braintree_webhook_secret_ref
        else:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        adapter = payment_processor(processor)
        event = adapter.verify_and_normalize(
            raw_body=request.body,
            signature_header=request.headers.get("X-Vokit-Payments-Signature", ""),
            secret_ref=secret_ref,
        )
        if event.chargeback:
            from control_plane.risk.infrastructure.container import apply_chargeback

            result = apply_chargeback().execute(event)
            return success(
                {
                    "duplicate": result.duplicate,
                    "status": result.status,
                    "invoice_id": result.invoice_id,
                    "customer_id": result.customer_id,
                    "agents_suspended": result.agents_suspended,
                }
            )
        if event.risk_flagged:
            from control_plane.risk.infrastructure.container import flag_risky_payment

            flagged = flag_risky_payment().execute(event)
            return success(
                {
                    "duplicate": flagged.duplicate,
                    "status": flagged.status,
                    "invoice_id": flagged.invoice_id,
                    "customer_id": flagged.customer_id,
                }
            )
        try:
            result = settle_payment().execute(event)
        except DomainError as exc:
            if exc.code == "processor_event_duplicate":
                return success(
                    {"duplicate": True, "status": "duplicate", "invoice_id": str(event.invoice_id)}
                )
            raise
        return success(
            {
                "duplicate": result.duplicate,
                "status": result.status,
                "invoice_id": result.invoice_id,
            }
        )
