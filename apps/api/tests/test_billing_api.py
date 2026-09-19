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
from tests.tenant_db_fixtures import platform_customer_body, tenant_db_payload

PASSWORD = "Phase2-Demo!ok"
STRIPE_REF = "STRIPE_WEBHOOK_SECRET"
BRAINTREE_REF = "BRAINTREE_WEBHOOK_SECRET"
SANDBOX_REF = "SANDBOX_WEBHOOK_SECRET"


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
    response = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": name,
            "legal_name": name,
            "owner_email": owner,
            "database": tenant_db_payload(owner),
        },
    )
    if response.status_code != 201:
        return response
    agency_id = response.json()["data"]["id"]
    return _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
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
    assert agency.status_code == 200
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency_id, "Cust A"),
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
    inbox = ctx["customer_client"].get("/api/v1/customer/notifications")
    assert inbox.status_code == 200
    assert (
        sum(1 for item in inbox.json()["data"] if item["event_type"] == "payment.success")
        == 1
    )


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
    assert other.status_code == 200
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
        platform_customer_body(other_id, "Cust C"),
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


@pytest.mark.django_db
def test_sandbox_pay_returns_hosted_url() -> None:
    ctx = _bootstrap_paid_ready()
    pay = _post(
        ctx["customer_client"],
        f"/api/v1/customer/invoices/{ctx['invoice_id']}/pay",
        {"processor": "sandbox"},
        HTTP_IDEMPOTENCY_KEY="pay-sandbox-url",
    )
    assert pay.status_code == 200
    data = pay.json()["data"]
    assert data["processor"] == "sandbox"
    assert data["hosted_url"].startswith("http://127.0.0.1:8081/checkout?")
    assert ctx["invoice_id"] in data["hosted_url"]
    assert "hosted_url" not in _post(
        ctx["customer_client"],
        f"/api/v1/customer/invoices/{ctx['invoice_id']}/pay",
        {"processor": "stripe"},
        HTTP_IDEMPOTENCY_KEY="pay-stripe-no-host",
    ).json()["data"]


@pytest.mark.django_db
def test_duplicate_sandbox_webhook_settles_once() -> None:
    ctx = _bootstrap_paid_ready()
    payload = {
        "event_id": "evt_sandbox_1",
        "invoice_id": ctx["invoice_id"],
        "amount_minor": ctx["amount_minor"],
        "currency": "USD",
        "status": "captured",
    }
    first = _webhook("sandbox", payload, secret_ref=SANDBOX_REF)
    assert first.status_code == 200
    assert first.json()["data"]["duplicate"] is False
    second = _webhook("sandbox", payload, secret_ref=SANDBOX_REF)
    assert second.status_code == 200
    assert second.json()["data"]["duplicate"] is True
    invoices = ctx["customer_client"].get("/api/v1/customer/invoices")
    assert invoices.json()["data"][0]["status"] == "paid"


@pytest.mark.django_db
def test_forged_sandbox_signature_is_rejected() -> None:
    ctx = _bootstrap_paid_ready()
    payload = {
        "event_id": "evt_sandbox_bad",
        "invoice_id": ctx["invoice_id"],
        "amount_minor": ctx["amount_minor"],
        "currency": "USD",
        "status": "captured",
    }
    forged = _webhook(
        "sandbox",
        payload,
        secret_ref=SANDBOX_REF,
        signature="sha256=00",
    )
    assert forged.status_code == 401
    assert forged.json()["error"]["code"] == "payment_signature_invalid"
    invoices = ctx["customer_client"].get("/api/v1/customer/invoices")
    assert invoices.json()["data"][0]["status"] == "open"


@pytest.mark.django_db
def test_sandbox_amount_mismatch_is_rejected() -> None:
    ctx = _bootstrap_paid_ready()
    payload = {
        "event_id": "evt_sandbox_mismatch",
        "invoice_id": ctx["invoice_id"],
        "amount_minor": ctx["amount_minor"] + 1,
        "currency": "USD",
        "status": "captured",
    }
    mismatch = _webhook("sandbox", payload, secret_ref=SANDBOX_REF)
    assert mismatch.status_code == 409
    assert mismatch.json()["error"]["code"] == "payment_amount_mismatch"
    invoices = ctx["customer_client"].get("/api/v1/customer/invoices")
    assert invoices.json()["data"][0]["status"] == "open"


def _subscription(client: Client, customer_id) -> dict:
    response = client.get(f"/api/v1/platform/customers/{customer_id}/subscription")
    assert response.status_code == 200
    return response.json()["data"]


def _add_version(client: Client, plan_id: str, **overrides) -> dict:
    body = _plan_body()
    body.update(overrides)
    response = _post(client, f"/api/v1/platform/plans/{plan_id}/versions", body)
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.django_db
def test_upgrade_applies_only_after_payment_and_keeps_old_invoice() -> None:
    ctx = _bootstrap_paid_ready()
    first_invoice = ctx["invoice_id"]
    current = _subscription(ctx["platform"], ctx["customer_id"])
    assert current["plan_version_id"] == ctx["version_id"]
    assert current["max_agents"] == 0
    assert current["pending_kind"] is None
    assert current["period_started_at"]
    v2 = _add_version(ctx["platform"], ctx["plan_id"], price_minor=20000)
    change = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{ctx['customer_id']}/subscription/change",
        {"plan_version_id": v2["id"]},
    )
    assert change.status_code == 201
    invoice = change.json()["data"]["invoice"]
    assert invoice["status"] == "open"
    assert invoice["due_at"] is not None
    kinds = {line["kind"] for line in invoice["lines"]}
    assert "subscription" in kinds
    assert "promo" in kinds
    assert invoice["total_minor"] < 20000
    assert invoice["total_minor"] == sum(line["amount_minor"] for line in invoice["lines"])
    pending = _subscription(ctx["platform"], ctx["customer_id"])
    assert pending["plan_version_id"] == ctx["version_id"]
    assert pending["pending_kind"] == "upgrade"
    assert pending["pending_plan_version_id"] == v2["id"]
    duplicate = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{ctx['customer_id']}/subscription",
        {"plan_version_id": v2["id"]},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "subscription_exists"
    customer_change = _post(
        ctx["customer_client"],
        f"/api/v1/platform/customers/{ctx['customer_id']}/subscription/change",
        {"plan_version_id": v2["id"]},
    )
    assert customer_change.status_code == 403
    paid = _webhook(
        "stripe",
        {
            "event_id": "evt_upgrade_1",
            "invoice_id": invoice["id"],
            "amount_minor": invoice["total_minor"],
            "currency": "USD",
            "status": "captured",
        },
        secret_ref=STRIPE_REF,
    )
    assert paid.status_code == 200
    switched = _subscription(ctx["platform"], ctx["customer_id"])
    assert switched["plan_version_id"] == v2["id"]
    assert switched["pending_kind"] is None
    invoices = ctx["customer_client"].get("/api/v1/customer/invoices")
    rows = {row["id"]: row for row in invoices.json()["data"]}
    assert rows[first_invoice]["status"] == "open"
    assert rows[first_invoice]["total_minor"] == 10000
    assert rows[invoice["id"]]["status"] == "paid"
    assert rows[invoice["id"]]["total_minor"] == invoice["total_minor"]


@pytest.mark.django_db
def test_expired_upgrade_invoice_stays_on_old_version() -> None:
    from dataclasses import replace
    from datetime import timedelta

    from django.utils import timezone

    from control_plane.billing.infrastructure.container import tenant_billing

    ctx = _bootstrap_paid_ready()
    v2 = _add_version(ctx["platform"], ctx["plan_id"], price_minor=25000)
    change = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{ctx['customer_id']}/subscription/change",
        {"plan_version_id": v2["id"]},
    )
    invoice_id = change.json()["data"]["invoice"]["id"]
    billing = tenant_billing()
    invoice = billing.get_invoice(ctx["agency_id"], uuid.UUID(invoice_id))
    assert invoice is not None
    billing.put_invoice(
        ctx["agency_id"],
        replace(invoice, due_at=timezone.now() - timedelta(seconds=1)),
    )
    expired = _post(
        ctx["customer_client"],
        f"/api/v1/customer/invoices/{invoice_id}/pay",
        {"processor": "stripe"},
        HTTP_IDEMPOTENCY_KEY="pay-expired-upgrade",
    )
    assert expired.status_code == 409
    assert expired.json()["error"]["code"] == "invoice_expired"
    current = _subscription(ctx["platform"], ctx["customer_id"])
    assert current["plan_version_id"] == ctx["version_id"]
    assert current["pending_kind"] is None
    retry = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{ctx['customer_id']}/subscription/change",
        {"plan_version_id": v2["id"]},
    )
    assert retry.status_code == 201
    assert retry.json()["data"]["invoice"]["id"] != invoice_id
    invoices = {
        row["id"]: row
        for row in ctx["customer_client"].get("/api/v1/customer/invoices").json()["data"]
    }
    assert invoices[invoice_id]["status"] == "void"


@pytest.mark.django_db
def test_cross_tenant_subscription_change_is_hidden() -> None:
    ctx = _bootstrap_paid_ready()
    other = _create_agency(ctx["platform"], "Bill D", "bill_d", "oa-bill-d@vokit.test")
    other_id = uuid.UUID(other.json()["data"]["id"])
    _user(
        "agency-d-bill@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=other_id,
    )
    agency_d = _client()
    _login(agency_d, "agency-d-bill@vokit.test")
    v2 = _add_version(ctx["platform"], ctx["plan_id"], price_minor=18000)
    denied = _post(
        agency_d,
        f"/api/v1/agency/customers/{ctx['customer_id']}/subscription/change",
        {"plan_version_id": v2["id"]},
    )
    assert denied.status_code == 404


@pytest.mark.django_db
def test_create_agent_without_subscription_is_allowed() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "No Sub", "no_sub", "oa-nosub@vokit.test")
    assert agency.status_code == 200
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(uuid.UUID(agency.json()["data"]["id"]), "No Sub Cust"),
    )
    assert customer.status_code == 201
    created = _post(
        platform,
        "/api/v1/platform/agents",
        {"customer_id": customer.json()["data"]["id"], "display_name": "Draft"},
    )
    assert created.status_code == 201


@pytest.mark.django_db
def test_active_agent_cap_and_scheduled_downgrade() -> None:
    from dataclasses import replace
    from datetime import timedelta

    from django.utils import timezone

    from control_plane.billing.infrastructure.container import tenant_billing

    ctx = _bootstrap_paid_ready()
    body = _plan_body()
    body["name"] = "Capped"
    body["max_agents"] = 2
    capped = _post(ctx["platform"], "/api/v1/platform/plans", body)
    assert capped.status_code == 201
    customer = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(ctx["agency_id"], "Cap Cust"),
    )
    customer_id = customer.json()["data"]["id"]
    assigned = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": capped.json()["data"]["versions"][0]["id"]},
    )
    assert assigned.status_code == 201
    first = _post(
        ctx["platform"],
        "/api/v1/platform/agents",
        {"customer_id": customer_id, "display_name": "One"},
    )
    second = _post(
        ctx["platform"],
        "/api/v1/platform/agents",
        {"customer_id": customer_id, "display_name": "Two"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{first.json()['data']['id']}/status",
        {"status": "active"},
    ).status_code == 200
    assert _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{second.json()['data']['id']}/status",
        {"status": "active"},
    ).status_code == 200
    blocked = _post(
        ctx["platform"],
        "/api/v1/platform/agents",
        {"customer_id": customer_id, "display_name": "Three"},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "plan_limit_agents"
    cheaper = _add_version(
        ctx["platform"],
        capped.json()["data"]["id"],
        price_minor=4000,
        max_agents=1,
    )
    extras = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{customer_id}/subscription/change",
        {"plan_version_id": cheaper["id"]},
    )
    assert extras.status_code == 409
    assert extras.json()["error"]["code"] == "extras_exceed_plan"
    paused = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{second.json()['data']['id']}/pause",
        {"reason": "fit downgrade"},
    )
    assert paused.status_code == 200
    scheduled = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{customer_id}/subscription/change",
        {"plan_version_id": cheaper["id"]},
    )
    assert scheduled.status_code == 200
    assert scheduled.json()["data"]["kind"] == "downgrade"
    pending = _subscription(ctx["platform"], customer_id)
    assert pending["pending_kind"] == "downgrade"
    assert pending["plan_version_id"] == capped.json()["data"]["versions"][0]["id"]
    billing = tenant_billing()
    row = billing.get_active_subscription(ctx["agency_id"], uuid.UUID(customer_id))
    assert row is not None
    billing.put_subscription(
        ctx["agency_id"],
        replace(row, pending_effective_at=timezone.now() - timedelta(seconds=1)),
    )
    applied = _subscription(ctx["platform"], customer_id)
    assert applied["plan_version_id"] == cheaper["id"]
    assert applied["pending_kind"] is None
    resume = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{second.json()['data']['id']}/status",
        {"status": "active"},
    )
    assert resume.status_code == 409
    assert resume.json()["error"]["code"] == "plan_limit_agents"


@pytest.mark.django_db
def test_payment_due_false_when_plan_paid_and_topup_open() -> None:
    ctx = _bootstrap_paid_ready()
    before = ctx["platform"].get(f"/api/v1/platform/customers/{ctx['customer_id']}")
    assert before.json()["data"]["payment_due"] is True
    pay = _post(
        ctx["customer_client"],
        f"/api/v1/customer/invoices/{ctx['invoice_id']}/pay",
        {"processor": "stripe"},
        HTTP_IDEMPOTENCY_KEY="pay-due-1",
    )
    assert pay.status_code == 200
    captured = _webhook(
        "stripe",
        {
            "event_id": "evt_pay_due_1",
            "invoice_id": ctx["invoice_id"],
            "amount_minor": ctx["amount_minor"],
            "currency": "USD",
            "status": "captured",
        },
        secret_ref=STRIPE_REF,
    )
    assert captured.status_code == 200
    topup = _post(
        ctx["customer_client"],
        "/api/v1/customer/usage/top-ups",
        {},
        HTTP_IDEMPOTENCY_KEY="topup-due-1",
    )
    assert topup.status_code == 201
    after = ctx["platform"].get(
        f"/api/v1/platform/customers/{ctx['customer_id']}/subscription"
    )
    assert after.status_code == 200
    assert after.json()["data"]["payment_due"] is False
    listed = ctx["platform"].get("/api/v1/platform/customers?payment_due=true")
    assert all(row["id"] != str(ctx["customer_id"]) for row in listed.json()["data"])


@pytest.mark.django_db
def test_uncaptured_webhook_notifies_failure_once() -> None:
    ctx = _bootstrap_paid_ready()
    _user(
        "agency-bill@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=ctx["agency_id"],
    )
    agency_client = _client()
    _login(agency_client, "agency-bill@vokit.test")
    payload = {
        "event_id": "evt_fail_1",
        "invoice_id": ctx["invoice_id"],
        "amount_minor": ctx["amount_minor"],
        "currency": "USD",
        "status": "failed",
    }
    first = _webhook("stripe", payload, secret_ref=STRIPE_REF)
    assert first.status_code == 409
    assert first.json()["error"]["code"] == "payment_not_captured"
    second = _webhook("stripe", payload, secret_ref=STRIPE_REF)
    assert second.status_code == 200
    assert second.json()["data"]["duplicate"] is True
    assert (
        sum(
            1
            for item in ctx["customer_client"].get("/api/v1/customer/notifications").json()["data"]
            if item["event_type"] == "payment.failure"
        )
        == 1
    )
    assert (
        sum(
            1
            for item in agency_client.get("/api/v1/agency/notifications").json()["data"]
            if item["event_type"] == "payment.failure"
        )
        == 1
    )


@pytest.mark.django_db
def test_minutes_low_notifies_once_on_threshold_cross() -> None:
    ctx = _bootstrap_paid_ready()
    _user(
        "agency-mins@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=ctx["agency_id"],
    )
    agency_client = _client()
    _login(agency_client, "agency-mins@vokit.test")
    credited = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{ctx['customer_id']}/minutes-adjustment",
        {"minutes": 12, "reason": "seed"},
    )
    assert credited.status_code == 201
    first = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{ctx['customer_id']}/minutes-adjustment",
        {"minutes": -5, "reason": "usage"},
    )
    assert first.status_code == 201
    assert first.json()["data"]["remaining_minutes"] == 7
    assert (
        sum(
            1
            for item in agency_client.get("/api/v1/agency/notifications").json()["data"]
            if item["event_type"] == "minutes.low"
        )
        == 1
    )
    second = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{ctx['customer_id']}/minutes-adjustment",
        {"minutes": -2, "reason": "more usage"},
    )
    assert second.status_code == 201
    assert (
        sum(
            1
            for item in agency_client.get("/api/v1/agency/notifications").json()["data"]
            if item["event_type"] == "minutes.low"
        )
        == 1
    )
