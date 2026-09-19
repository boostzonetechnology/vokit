from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from control_plane.billing.application.add_plan_version import (
    AddPlanVersionCommand,
    UpdatePlanVersionCommand,
)
from control_plane.billing.application.assign_subscription import AssignSubscriptionCommand
from control_plane.billing.application.change_subscription import ChangeSubscriptionCommand
from control_plane.billing.application.create_plan import CreatePlanCommand
from control_plane.billing.application.create_topup import CreateTopUpCommand
from control_plane.billing.application.pay_invoice import PayInvoiceCommand
from control_plane.billing.domain.lots import LotBalance, remaining_minutes
from control_plane.billing.domain.policies import assigned_plan_is_payment_due
from control_plane.billing.domain.types import DRAIN_ORDER, InvoiceStatus, PlanStatus
from control_plane.billing.infrastructure.container import (
    add_plan_version,
    archive_plan,
    assign_subscription,
    billing_settings,
    change_subscription,
    create_plan,
    create_topup,
    get_customer_subscription,
    invoice_index,
    pay_invoice,
    payment_processor,
    plan_versions,
    plans,
    settle_payment,
    tenant_billing,
    update_plan_version,
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
from control_plane.integrations.domain.types import ProviderKind
from providers.billing.sandbox import sandbox_checkout_url
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page
from tenant.billing.domain import InvoiceRecord


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


def _integrations_field(data: dict) -> tuple[str, ...]:
    raw = data.get("allowed_integrations", [])
    if raw is None:
        return ()
    if type(raw) is not list:
        raise DomainError("validation_error", "allowed_integrations must be a list.")
    slugs: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if type(item) is not str:
            raise DomainError("validation_error", "allowed_integrations must be strings.")
        slug = item.strip()
        if not slug or slug in seen:
            continue
        try:
            ProviderKind(slug)
        except ValueError as exc:
            raise DomainError(
                "validation_error", "allowed_integrations contains an unknown provider."
            ) from exc
        seen.add(slug)
        slugs.append(slug)
    return tuple(slugs)


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
        "max_agents": _int_field(data, "max_agents", 0),
        "max_phone_numbers": _int_field(data, "max_phone_numbers", 0),
        "max_concurrency": _int_field(data, "max_concurrency", 0),
        "recording_allowed": _bool_field(data, "recording_allowed", True),
        "allowed_integrations": _integrations_field(data),
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
        "max_agents": row.max_agents,
        "max_phone_numbers": row.max_phone_numbers,
        "max_concurrency": row.max_concurrency,
        "recording_allowed": row.recording_allowed,
        "allowed_integrations": list(row.allowed_integrations),
        "used": row.used_at is not None,
    }


def _plan_payload(row) -> dict[str, object]:
    versions = [_version_payload(item) for item in plan_versions().list_for_plan(row.id)]
    return {
        "id": str(row.id),
        "name": row.name,
        "status": row.status.value,
        "versions": versions,
        "available_integrations": [kind.value for kind in ProviderKind],
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
        "due_at": row.due_at.isoformat() if getattr(row, "due_at", None) else None,
    }


def _subscription_payload(view) -> dict[str, object]:
    sub = view.subscription
    version = view.version
    return {
        "id": str(sub.subscription_id),
        "customer_id": str(sub.customer_id),
        "agency_id": str(sub.tenant_id),
        "plan_id": str(sub.plan_id),
        "plan_version_id": str(sub.plan_version_id),
        "plan_name": view.plan_name,
        "plan_version": view.plan_version,
        "status": sub.status.value,
        "cycle": sub.cycle,
        "included_minutes": view.included_minutes,
        "max_agents": version.max_agents,
        "max_phone_numbers": version.max_phone_numbers,
        "max_concurrency": version.max_concurrency,
        "recording_allowed": version.recording_allowed,
        "allowed_integrations": list(version.allowed_integrations),
        "period_started_at": sub.period_started_at.isoformat()
        if sub.period_started_at
        else (sub.created_at.isoformat() if sub.created_at else None),
        "period_end": view.period_end.isoformat() if view.period_end else None,
        "pending_kind": sub.pending_kind,
        "pending_plan_version_id": str(sub.pending_plan_version_id)
        if sub.pending_plan_version_id
        else None,
        "pending_invoice_id": str(sub.pending_invoice_id) if sub.pending_invoice_id else None,
        "pending_effective_at": sub.pending_effective_at.isoformat()
        if sub.pending_effective_at
        else None,
        "payment_due": assigned_plan_is_payment_due(
            sub.subscription_id,
            tenant_billing().list_invoices(sub.tenant_id, sub.customer_id),
        ),
    }


def _change_response(command: ChangeSubscriptionCommand) -> Response:
    result = change_subscription().execute(command)
    payload: dict[str, object] = {"kind": result.kind}
    if result.invoice is not None:
        payload["invoice"] = _invoice_payload(result.invoice)
        return success(payload, status=201)
    view = get_customer_subscription().execute(result.subscription.customer_id)
    payload["subscription"] = _subscription_payload(view) if view else None
    return success(payload)


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
        require_platform_perm(request, "plan.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows, page = page_slice(plans().list(), offset, limit)
        return success([_plan_payload(row) for row in rows], page=page)

    def post(self, request: Request) -> Response:
        require_platform_perm(request, "plan.create")
        plan, _version = create_plan().execute(
            CreatePlanCommand(name=str(request.data.get("name") or ""), **_plan_terms(request.data))
        )
        return success(_plan_payload(plan), status=201)


class PlatformPlanVersionView(CsrfAPIView):
    def post(self, request: Request, plan_id: str) -> Response:
        require_platform_perm(request, "plan.create")
        version = add_plan_version().execute(
            AddPlanVersionCommand(
                plan_id=parse_uuid(plan_id, field="plan_id"),
                **_plan_terms(request.data),
            )
        )
        return success(_version_payload(version), status=201)


class PlatformPlanVersionDetailView(CsrfAPIView):
    def patch(self, request: Request, version_id: str) -> Response:
        require_platform_perm(request, "plan.update")
        version = update_plan_version().execute(
            UpdatePlanVersionCommand(
                version_id=parse_uuid(version_id, field="version_id"),
                **_plan_terms(request.data),
            )
        )
        return success(_version_payload(version))


class PlatformPlanArchiveView(CsrfAPIView):
    def post(self, request: Request, plan_id: str) -> Response:
        require_platform_perm(request, "plan.update")
        plan = archive_plan().execute(parse_uuid(plan_id, field="plan_id"))
        return success(_plan_payload(plan))


class PlatformCustomerSubscriptionView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        require_platform_perm(request, "customer.view")
        view = get_customer_subscription().execute(
            parse_uuid(customer_id, field="customer_id")
        )
        if view is None:
            return success(None)
        return success(_subscription_payload(view))

    def post(self, request: Request, customer_id: str) -> Response:
        require_platform_perm(request, "customer.create")
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


class PlatformCustomerSubscriptionChangeView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        require_platform_perm(request, "customer.create")
        return _change_response(
            ChangeSubscriptionCommand(
                customer_id=parse_uuid(customer_id, field="customer_id"),
                plan_version_id=parse_uuid(
                    request.data.get("plan_version_id"), field="plan_version_id"
                ),
                actor_tenant_id=None,
                privileged=True,
            )
        )


class PlatformInvoiceCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "billing.view")
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
        require_platform_perm(request, "billing.view")
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

        require_platform_perm(request, "billing.view")
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
        require_agency_perm(request, "customer.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows, page = page_slice(plans().list(status=PlanStatus.ACTIVE), offset, limit)
        return success([_plan_payload(row) for row in rows], page=page)


class AgencyCustomerSubscriptionView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "customer.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        identifier = parse_uuid(customer_id, field="customer_id")
        indexed = customer_index().get(identifier)
        if indexed is None or indexed.tenant_id != tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        view = get_customer_subscription().execute(identifier)
        if view is None:
            return success(None)
        return success(_subscription_payload(view))

    def post(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "customer.update")
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


class AgencyCustomerSubscriptionChangeView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "customer.update")
        return _change_response(
            ChangeSubscriptionCommand(
                customer_id=parse_uuid(customer_id, field="customer_id"),
                plan_version_id=parse_uuid(
                    request.data.get("plan_version_id"), field="plan_version_id"
                ),
                actor_tenant_id=context.membership.tenant_id,
                privileged=False,
            )
        )


class AgencyCustomerInvoiceCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "customer.view")
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
        context = require_customer_perm(request, "billing.pay")
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
        context = require_customer_perm(request, "billing.pay")
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
        payload = {
            "invoice_id": str(intent.invoice.invoice_id),
            "processor": intent.processor,
            "amount_minor": intent.invoice.total_minor,
            "currency": intent.invoice.currency,
            "client_reference": intent.client_reference,
            "status": "awaiting_webhook",
        }
        if intent.processor == "sandbox":
            hosted_url = sandbox_checkout_url(
                invoice_id=str(intent.invoice.invoice_id),
                amount_minor=intent.invoice.total_minor,
                currency=intent.invoice.currency,
                client_reference=intent.client_reference,
            )
            if hosted_url:
                payload["hosted_url"] = hosted_url
        return success(payload)


class CustomerTopUpView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_customer_perm(request, "billing.pay")
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
        context = require_customer_perm(request, "billing.pay")
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
        require_customer_perm(request, "billing.pay")
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
        elif processor == "sandbox":
            secret_ref = settings_row.sandbox_webhook_secret_ref
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
