from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from shared_kernel.hmac import sign_hmac_sha256
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"
STRIPE_REF = "STRIPE_WEBHOOK_SECRET"
BRAINTREE_REF = "BRAINTREE_WEBHOOK_SECRET"


def _client() -> Client:
    return Client(enforce_csrf_checks=True)


def _csrf(client: Client) -> str:
    return client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]


def _post(client: Client, path: str, payload: dict, **headers):
    extra = {"HTTP_X_CSRFTOKEN": _csrf(client)}
    extra.update(headers)
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        **extra,
    )


def _patch(client: Client, path: str, payload: dict):
    return client.patch(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(client),
    )


def _user(
    email: str,
    principal: PrincipalType,
    role: str,
    tenant_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
) -> User:
    user = User.objects.create_user(email=email, password=PASSWORD)
    DjangoMembershipRepository().create(
        MembershipRecord(
            id=new_uuid7(),
            user_id=user.id,
            principal_type=principal,
            role=role,
            tenant_id=tenant_id,
            customer_id=customer_id,
            status=MembershipStatus.ACTIVE,
        )
    )
    return user


def _login(client: Client, email: str) -> None:
    login = _post(client, "/api/v1/auth/login", {"email": email, "password": PASSWORD})
    assert login.status_code == 200


def _create_agency(client: Client, name: str, db_name: str, owner: str):
    _ = db_name
    return _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": name,
            "legal_name": name,
            "owner_email": owner,
        },
    )


def _plan_body() -> dict:
    return {
        "name": "Starter",
        "price_minor": 10000,
        "included_minutes": 100,
        "allow_topups": True,
        "topup_minutes": 50,
        "topup_price_minor": 2000,
        "overage_enabled": False,
        "overage_price_per_minute_minor": 0,
        "grace_seconds": 30,
    }


def _webhook(processor: str, payload: dict, *, secret_ref: str, signature: str | None = None):
    body = json.dumps(payload).encode()
    header = signature
    if header is None:
        header = sign_hmac_sha256(secret_ref=secret_ref, raw_body=body)
    client = Client(enforce_csrf_checks=True)
    return client.post(
        f"/webhooks/{processor}/v1/",
        data=body,
        content_type="application/json",
        HTTP_X_VOKIT_PAYMENTS_SIGNATURE=header,
    )


def _bootstrap_paid_ready():
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Bill A", "bill_a", "oa-bill@vokit.test")
    assert agency.status_code == 201
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Cust A", "agency_id": str(agency_id)},
    )
    assert customer.status_code == 201
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    plan = _post(platform, "/api/v1/platform/plans", _plan_body())
    assert plan.status_code == 201
    version_id = plan.json()["data"]["versions"][0]["id"]
    assigned = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": version_id},
    )
    assert assigned.status_code == 201
    invoice_id = assigned.json()["data"]["id"]
    _user(
        "cust-bill@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=agency_id,
        customer_id=customer_id,
    )
    customer_client = _client()
    _login(customer_client, "cust-bill@vokit.test")
    return {
        "platform": platform,
        "agency_id": agency_id,
        "customer_id": customer_id,
        "customer_client": customer_client,
        "invoice_id": invoice_id,
        "version_id": version_id,
        "plan_id": plan.json()["data"]["id"],
        "amount_minor": assigned.json()["data"]["total_minor"],
    }


@pytest.mark.django_db
def test_duplicate_stripe_webhook_settles_once() -> None:
    ctx = _bootstrap_paid_ready()
    pay = _post(
        ctx["customer_client"],
        f"/api/v1/customer/invoices/{ctx['invoice_id']}/pay",
        {"processor": "stripe"},
        HTTP_IDEMPOTENCY_KEY="pay-1",
    )
    assert pay.status_code == 200
    payload = {
        "event_id": "evt_stripe_1",
        "invoice_id": ctx["invoice_id"],
        "amount_minor": ctx["amount_minor"],
        "currency": "USD",
        "status": "captured",
    }
    first = _webhook("stripe", payload, secret_ref=STRIPE_REF)
    assert first.status_code == 200
    assert first.json()["data"]["duplicate"] is False
    second = _webhook("stripe", payload, secret_ref=STRIPE_REF)
    assert second.status_code == 200
    assert second.json()["data"]["duplicate"] is True
    invoices = ctx["customer_client"].get("/api/v1/customer/invoices")
    assert invoices.status_code == 200
    rows = invoices.json()["data"]
    assert len(rows) == 1
    assert rows[0]["status"] == "paid"
    assert rows[0]["total_minor"] == 10000
    usage = ctx["customer_client"].get("/api/v1/customer/usage")
    assert usage.json()["data"]["remaining_minutes"] == 100
    payments = ctx["platform"].get("/api/v1/platform/payments")
    assert payments.status_code == 200
    assert len(payments.json()["data"]) == 1


@pytest.mark.django_db
def test_duplicate_braintree_webhook_settles_once() -> None:
    ctx = _bootstrap_paid_ready()
    payload = {
        "event_id": "evt_bt_1",
        "invoice_id": ctx["invoice_id"],
        "amount_minor": ctx["amount_minor"],
        "currency": "USD",
        "status": "settled",
    }
    first = _webhook("braintree", payload, secret_ref=BRAINTREE_REF)
    assert first.status_code == 200
    assert first.json()["data"]["duplicate"] is False
    second = _webhook("braintree", payload, secret_ref=BRAINTREE_REF)
    assert second.status_code == 200
    assert second.json()["data"]["duplicate"] is True
    invoices = ctx["customer_client"].get("/api/v1/customer/invoices")
    assert invoices.json()["data"][0]["status"] == "paid"


@pytest.mark.django_db
def test_forged_payment_signature_is_rejected() -> None:
    ctx = _bootstrap_paid_ready()
    payload = {
        "event_id": "evt_bad",
        "invoice_id": ctx["invoice_id"],
        "amount_minor": ctx["amount_minor"],
        "currency": "USD",
        "status": "captured",
    }
    forged = _webhook("stripe", payload, secret_ref=STRIPE_REF, signature="sha256=00")
    assert forged.status_code == 401
    assert forged.json()["error"]["code"] == "payment_signature_invalid"
    invoices = ctx["customer_client"].get("/api/v1/customer/invoices")
    assert invoices.json()["data"][0]["status"] == "open"


@pytest.mark.django_db
def test_agency_cannot_see_other_agency_invoices() -> None:
    ctx = _bootstrap_paid_ready()
    other = _create_agency(ctx["platform"], "Bill B", "bill_b", "oa-bill-b@vokit.test")
    assert other.status_code == 201
    other_id = uuid.UUID(other.json()["data"]["id"])
    _user(
        "agency-b-bill@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=other_id,
    )
    agency_b = _client()
    _login(agency_b, "agency-b-bill@vokit.test")
    visible = agency_b.get("/api/v1/agency/customer-invoices")
    assert visible.status_code == 200
    assert visible.json()["data"] == []


@pytest.mark.django_db
def test_customer_cannot_pay_foreign_invoice() -> None:
    ctx = _bootstrap_paid_ready()
    other = _create_agency(ctx["platform"], "Bill C", "bill_c", "oa-bill-c@vokit.test")
    other_id = uuid.UUID(other.json()["data"]["id"])
    other_customer = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        {"display_name": "Cust C", "agency_id": str(other_id)},
    )
    other_customer_id = uuid.UUID(other_customer.json()["data"]["id"])
    _user(
        "cust-c@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=other_id,
        customer_id=other_customer_id,
    )
    foreign = _client()
    _login(foreign, "cust-c@vokit.test")
    denied = _post(
        foreign,
        f"/api/v1/customer/invoices/{ctx['invoice_id']}/pay",
        {"processor": "stripe"},
        HTTP_IDEMPOTENCY_KEY="pay-foreign",
    )
    assert denied.status_code == 404


@pytest.mark.django_db
def test_used_plan_version_cannot_be_patched() -> None:
    ctx = _bootstrap_paid_ready()
    body = _plan_body()
    body["price_minor"] = 1
    denied = _patch(
        ctx["platform"],
        f"/api/v1/platform/plan-versions/{ctx['version_id']}",
        body,
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "plan_version_immutable"


@pytest.mark.django_db
def test_topup_settles_into_a_second_lot() -> None:
    ctx = _bootstrap_paid_ready()
    first_pay = {
        "event_id": "evt_sub",
        "invoice_id": ctx["invoice_id"],
        "amount_minor": ctx["amount_minor"],
        "currency": "USD",
        "status": "captured",
    }
    assert _webhook("stripe", first_pay, secret_ref=STRIPE_REF).status_code == 200
    topup = _post(
        ctx["customer_client"],
        "/api/v1/customer/usage/top-ups",
        {},
        HTTP_IDEMPOTENCY_KEY="top-1",
    )
    assert topup.status_code == 201
    topup_id = topup.json()["data"]["id"]
    assert topup.json()["data"]["total_minor"] == 2000
    assert _webhook(
        "stripe",
        {
            "event_id": "evt_top",
            "invoice_id": topup_id,
            "amount_minor": 2000,
            "currency": "USD",
            "status": "captured",
        },
        secret_ref=STRIPE_REF,
    ).status_code == 200
    usage = ctx["customer_client"].get("/api/v1/customer/usage")
    assert usage.json()["data"]["remaining_minutes"] == 150
    kinds = {lot["kind"] for lot in usage.json()["data"]["lots"]}
    assert kinds == {"included", "topup"}


@pytest.mark.django_db
def test_finance_admin_can_view_invoices_not_create_plans() -> None:
    _bootstrap_paid_ready()
    _user("finance-bill@vokit.test", PrincipalType.PLATFORM, "finance_admin")
    finance = _client()
    _login(finance, "finance-bill@vokit.test")
    invoices = finance.get("/api/v1/platform/invoices")
    assert invoices.status_code == 200
    assert len(invoices.json()["data"]) == 1
    denied = _post(finance, "/api/v1/platform/plans", _plan_body())
    assert denied.status_code == 403
