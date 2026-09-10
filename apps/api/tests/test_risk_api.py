from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.commission.domain.types import LedgerKind
from control_plane.commission.models import LedgerEntry
from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.risk.models import RiskCase, VerificationSubmission
from shared_kernel.hmac import sign_hmac_sha256
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"
STRIPE_REF = "STRIPE_WEBHOOK_SECRET"


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
            "commission_rate_bps": 3000,
        },
    )


def _webhook(payload: dict, *, signature: str | None = None):
    body = json.dumps(payload).encode()
    header = signature
    if header is None:
        header = sign_hmac_sha256(secret_ref=STRIPE_REF, raw_body=body)
    return Client(enforce_csrf_checks=True).post(
        "/webhooks/stripe/v1/",
        data=body,
        content_type="application/json",
        HTTP_X_VOKIT_PAYMENTS_SIGNATURE=header,
    )


def _plan_body() -> dict:
    return {
        "name": "Risk Starter",
        "price_minor": 10000,
        "included_minutes": 100,
        "allow_topups": True,
        "topup_minutes": 50,
        "topup_price_minor": 2000,
        "overage_enabled": False,
        "overage_price_per_minute_minor": 0,
        "grace_seconds": 0,
    }


def _bootstrap():
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Risk A", "risk_a", "oa-risk@vokit.test")
    assert agency.status_code == 201
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Cust Risk", "agency_id": str(agency_id)},
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
        "agency-risk@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    _user(
        "cust-risk@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=agency_id,
        customer_id=customer_id,
    )
    agency_client = _client()
    _login(agency_client, "agency-risk@vokit.test")
    customer_client = _client()
    _login(customer_client, "cust-risk@vokit.test")
    return {
        "platform": platform,
        "agency_id": agency_id,
        "customer_id": customer_id,
        "agency_client": agency_client,
        "customer_client": customer_client,
        "invoice_id": invoice_id,
        "version_id": version_id,
        "amount_minor": assigned.json()["data"]["total_minor"],
    }


def _pay(invoice_id: str, amount_minor: int, event_id: str):
    paid = _webhook(
        {
            "event_id": event_id,
            "invoice_id": invoice_id,
            "amount_minor": amount_minor,
            "currency": "USD",
            "status": "captured",
        }
    )
    assert paid.status_code == 200
    return paid


@pytest.mark.django_db
def test_chargeback_disables_agents_and_reverses_commission() -> None:
    ctx = _bootstrap()
    _pay(ctx["invoice_id"], ctx["amount_minor"], "evt-risk-pay")
    assert LedgerEntry.objects.filter(kind=LedgerKind.COMMISSION_EARNED.value).count() == 1
    created = _post(
        ctx["agency_client"],
        f"/api/v1/agency/customers/{ctx['customer_id']}/agents",
        {"display_name": "Support bot"},
    )
    assert created.status_code == 201
    assert created.json()["data"]["status"] == "draft"
    topup = _post(
        ctx["customer_client"],
        "/api/v1/customer/usage/top-ups",
        {},
        HTTP_IDEMPOTENCY_KEY="topup-risk-1",
    )
    assert topup.status_code == 201
    chargeback = _webhook(
        {
            "event_id": "dp_risk_1",
            "invoice_id": ctx["invoice_id"],
            "amount_minor": ctx["amount_minor"],
            "currency": "USD",
            "status": "chargeback.confirmed",
        }
    )
    assert chargeback.status_code == 200
    assert chargeback.json()["data"]["duplicate"] is False
    assert chargeback.json()["data"]["agents_suspended"] == 1
    agents = ctx["agency_client"].get(
        f"/api/v1/agency/customers/{ctx['customer_id']}/agents"
    )
    assert agents.status_code == 200
    assert agents.json()["data"][0]["status"] == "suspended"
    case = RiskCase.objects.get(customer_id=ctx["customer_id"])
    assert case.status == "chargeback_frozen"
    assert case.permanently_banned is True
    assert LedgerEntry.objects.filter(kind=LedgerKind.COMMISSION_REVERSAL.value).count() == 1
    replay = _webhook(
        {
            "event_id": "dp_risk_1",
            "invoice_id": ctx["invoice_id"],
            "amount_minor": ctx["amount_minor"],
            "currency": "USD",
            "status": "chargeback.confirmed",
        }
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["duplicate"] is True
    assert LedgerEntry.objects.filter(kind=LedgerKind.COMMISSION_REVERSAL.value).count() == 1
    blocked_agent = _post(
        ctx["agency_client"],
        f"/api/v1/agency/customers/{ctx['customer_id']}/agents",
        {"display_name": "Second bot"},
    )
    assert blocked_agent.status_code == 409
    assert blocked_agent.json()["error"]["code"] == "customer_risk_blocked"
    blocked_topup = _post(
        ctx["customer_client"],
        "/api/v1/customer/usage/top-ups",
        {},
        HTTP_IDEMPOTENCY_KEY="topup-risk-2",
    )
    assert blocked_topup.status_code == 409
    assert blocked_topup.json()["error"]["code"] == "customer_risk_blocked"
    blocked_pay = _post(
        ctx["customer_client"],
        f"/api/v1/customer/invoices/{topup.json()['data']['id']}/pay",
        {"processor": "stripe"},
        HTTP_IDEMPOTENCY_KEY="pay-risk-frozen",
    )
    assert blocked_pay.status_code == 409
    assert blocked_pay.json()["error"]["code"] == "customer_risk_blocked"
    other = _create_agency(ctx["platform"], "Risk B", "risk_b", "oa-risk-b@vokit.test")
    assert other.status_code == 201
    denied = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        {
            "display_name": "Replay",
            "agency_id": other.json()["data"]["id"],
            "owner_email": "cust-risk@vokit.test",
        },
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "customer_ineligible"
    override = _post(
        ctx["agency_client"],
        f"/api/v1/agency/customers/{ctx['customer_id']}/risk/override",
        {"status": "verified"},
    )
    assert override.status_code == 403
    assert override.json()["error"]["code"] == "forbidden"
    disputes = ctx["platform"].get("/api/v1/platform/disputes")
    assert disputes.status_code == 200
    assert disputes.json()["data"][0]["event_id"] == "dp_risk_1"


@pytest.mark.django_db
def test_over_exposed_card_image_is_rejected_and_not_submitted() -> None:
    ctx = _bootstrap()
    rejected = _post(
        ctx["customer_client"],
        "/api/v1/customer/verification",
        {
            "id_object_ref": "obj_id_1",
            "id_content_type": "image/jpeg",
            "id_checksum": "abc123",
            "card_object_ref": "obj_card_1",
            "card_checksum": "def456",
            "card_last4": "4242",
            "visible_digit_count": 16,
            "cvv_visible": False,
            "full_pan_present": False,
        },
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "card_image_unmasked"
    assert VerificationSubmission.objects.count() == 0
    current = ctx["customer_client"].get("/api/v1/customer/verification")
    assert current.status_code == 200
    assert current.json()["data"]["status"] == "incomplete"
    accepted = _post(
        ctx["customer_client"],
        "/api/v1/customer/verification",
        {
            "id_object_ref": "obj_id_1",
            "id_content_type": "image/jpeg",
            "id_checksum": "abc123",
            "card_object_ref": "obj_card_1",
            "card_checksum": "def456",
            "card_last4": "4242",
            "visible_digit_count": 4,
            "cvv_visible": False,
            "full_pan_present": False,
        },
    )
    assert accepted.status_code == 201
    assert accepted.json()["data"]["status"] == "submitted"
    assert accepted.json()["data"]["card_last4"] == "4242"
    risk = ctx["customer_client"].get("/api/v1/customer/risk")
    assert risk.json()["data"]["status"] == "verification_submitted"


@pytest.mark.django_db
def test_forged_chargeback_signature_is_rejected() -> None:
    ctx = _bootstrap()
    forged = _webhook(
        {
            "event_id": "dp_forged",
            "invoice_id": ctx["invoice_id"],
            "amount_minor": ctx["amount_minor"],
            "currency": "USD",
            "status": "chargeback.confirmed",
        },
        signature="sha256=00",
    )
    assert forged.status_code == 401
    assert forged.json()["error"]["code"] == "payment_signature_invalid"
    assert RiskCase.objects.count() == 0
    assert LedgerEntry.objects.filter(kind=LedgerKind.COMMISSION_REVERSAL.value).count() == 0
