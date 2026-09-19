from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from django.test import Client

from control_plane.commission.application.release_holds import ReleaseHolds
from control_plane.commission.domain.types import LedgerKind
from control_plane.commission.infrastructure.container import ledger
from control_plane.commission.models import LedgerEntry
from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.kyc.infrastructure.hmac import sign_kyc_body
from control_plane.tenancy.infrastructure.container import tenant_repo
from shared_kernel.hmac import sign_hmac_sha256
from shared_kernel.ids import new_uuid7
from tests.tenant_db_fixtures import platform_customer_body, tenant_db_payload

PASSWORD = "Phase2-Demo!ok"
STRIPE_REF = "STRIPE_WEBHOOK_SECRET"
KYC_REF = "KYC_WEBHOOK_SECRET"


class _Clock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


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
            "commission_rate_bps": 3000,
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


def _pay_invoice(invoice_id: str, amount_minor: int, event_id: str):
    body = json.dumps(
        {
            "event_id": event_id,
            "invoice_id": invoice_id,
            "amount_minor": amount_minor,
            "currency": "USD",
            "status": "captured",
        }
    ).encode()
    header = sign_hmac_sha256(secret_ref=STRIPE_REF, raw_body=body)
    return Client(enforce_csrf_checks=True).post(
        "/webhooks/stripe/v1/",
        data=body,
        content_type="application/json",
        HTTP_X_VOKIT_PAYMENTS_SIGNATURE=header,
    )


def _verify_kyc(agency_client: Client) -> None:
    session = _post(agency_client, "/api/v1/agency/kyc/session", {})
    assert session.status_code == 201
    payload = {
        "event_id": str(new_uuid7()),
        "session_id": session.json()["data"]["session_id"],
        "status": "verified",
    }
    body = json.dumps(payload).encode()
    header = sign_kyc_body(secret_ref=KYC_REF, raw_body=body)
    hook = Client(enforce_csrf_checks=True).post(
        "/webhooks/kyc/external/v1/",
        data=body,
        content_type="application/json",
        HTTP_X_VOKIT_KYC_SIGNATURE=header,
    )
    assert hook.status_code == 200


def _ready_paid_agency(*, hold_days: int | None = None):
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Comm A", "comm_a", "oa-comm@vokit.test")
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency_id, "Cust A"),
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": "Pro",
            "price_minor": 10000,
            "included_minutes": 100,
            "allow_topups": False,
            "topup_minutes": 0,
            "topup_price_minor": 0,
            "overage_enabled": False,
            "overage_price_per_minute_minor": 0,
            "grace_seconds": 0,
        },
    )
    version_id = plan.json()["data"]["versions"][0]["id"]
    assigned = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": version_id},
    )
    invoice_id = assigned.json()["data"]["id"]
    _user(
        "agency-comm@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    agency_client = _client()
    _login(agency_client, "agency-comm@vokit.test")
    if hold_days is not None:
        changed = _patch(
            platform,
            "/api/v1/platform/settings",
            {"key": "payout.hold_days", "value": hold_days, "reason": "hold policy"},
        )
        assert changed.status_code == 200
    paid = _pay_invoice(invoice_id, 10000, "evt-comm-1")
    assert paid.status_code == 200
    return platform, agency_id, agency_client


def _request_payout(agency_client: Client, *, key: str = "po-1", amount_minor: int = 3000):
    _verify_kyc(agency_client)
    ReleaseHolds(ledger(), tenant_repo(), _Clock(datetime.now(UTC) + timedelta(days=16))).execute()
    requested = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": amount_minor, "method_label": "bank ****1111"},
        HTTP_IDEMPOTENCY_KEY=key,
    )
    assert requested.status_code == 201
    return requested.json()["data"]["id"]


def _event_count(client: Client, path: str, event_type: str) -> int:
    inbox = client.get(path)
    assert inbox.status_code == 200
    return sum(1 for item in inbox.json()["data"] if item["event_type"] == event_type)


@pytest.mark.django_db
def test_duplicate_payment_creates_one_commission() -> None:
    _ready_paid_agency()
    replay = _pay_invoice(
        str(LedgerEntry.objects.get(kind=LedgerKind.COMMISSION_EARNED.value).invoice_id),
        10000,
        "evt-comm-1",
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["duplicate"] is True
    assert LedgerEntry.objects.filter(kind=LedgerKind.COMMISSION_EARNED.value).count() == 1
    row = LedgerEntry.objects.get(kind=LedgerKind.COMMISSION_EARNED.value)
    assert row.amount_minor == 3000
    assert row.eligible_base_minor == 10000
    assert row.rate_bps_snapshot == 3000


@pytest.mark.django_db
def test_agency_cannot_fetch_payout_proof() -> None:
    platform, agency_id, agency_client = _ready_paid_agency()
    _verify_kyc(agency_client)
    ReleaseHolds(ledger(), tenant_repo(), _Clock(datetime.now(UTC) + timedelta(days=16))).execute()
    requested = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000, "method_label": "bank ****1111"},
        HTTP_IDEMPOTENCY_KEY="po-1",
    )
    assert requested.status_code == 201
    payout_id = requested.json()["data"]["id"]
    proof = _post(
        platform,
        f"/api/v1/platform/payouts/{payout_id}/proof",
        {
            "object_ref": f"payout/{payout_id}/proof/a",
            "content_type": "application/pdf",
            "checksum": "sha256:abc",
        },
    )
    assert proof.status_code == 201
    denied = agency_client.get(f"/api/v1/agency/payouts/{payout_id}/proof")
    assert denied.status_code == 404
    assert "object_ref" not in json.dumps(denied.json())
    _post(platform, f"/api/v1/platform/payouts/{payout_id}/action", {"action": "approve"})
    paid = _post(
        platform,
        f"/api/v1/platform/payouts/{payout_id}/mark-paid",
        {"transaction_ref": "ach-1"},
    )
    assert paid.status_code == 200
    assert paid.json()["data"]["status"] == "paid"
    receipt = agency_client.get(f"/api/v1/agency/payouts/{payout_id}/receipt")
    assert receipt.status_code == 200
    data = receipt.json()["data"]
    assert data["receipt_number"].startswith("VKT-PO-")
    assert data["agency_display_name"] == "Comm A"
    assert data["issuer"] == "Vokit"
    assert data["method_label"] == "bank ****1111"
    assert data["transaction_ref"] == "*ch-1"
    assert "banking proof" in data["disclaimer"]
    assert _event_count(agency_client, "/api/v1/agency/notifications", "payout.paid") == 1


@pytest.mark.django_db
def test_concurrent_payouts_cannot_over_reserve() -> None:
    _platform, _agency_id, agency_client = _ready_paid_agency()
    _verify_kyc(agency_client)
    ReleaseHolds(ledger(), tenant_repo(), _Clock(datetime.now(UTC) + timedelta(days=16))).execute()
    first = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000},
        HTTP_IDEMPOTENCY_KEY="po-a",
    )
    assert first.status_code == 201
    second = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000},
        HTTP_IDEMPOTENCY_KEY="po-b",
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "payout_insufficient"


@pytest.mark.django_db
def test_mark_paid_is_blocked_without_proof() -> None:
    platform, _agency_id, agency_client = _ready_paid_agency()
    _verify_kyc(agency_client)
    ReleaseHolds(ledger(), tenant_repo(), _Clock(datetime.now(UTC) + timedelta(days=16))).execute()
    requested = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000, "method_label": "bank ****1111"},
        HTTP_IDEMPOTENCY_KEY="po-noproof",
    )
    payout_id = requested.json()["data"]["id"]
    _post(platform, f"/api/v1/platform/payouts/{payout_id}/action", {"action": "approve"})
    paid = _post(
        platform,
        f"/api/v1/platform/payouts/{payout_id}/mark-paid",
        {"transaction_ref": "ach-missing"},
    )
    assert paid.status_code == 409
    assert paid.json()["error"]["code"] == "payout_proof_required"


@pytest.mark.django_db
def test_settlement_uses_configured_hold_days() -> None:
    _ready_paid_agency(hold_days=21)
    row = LedgerEntry.objects.get(kind=LedgerKind.COMMISSION_EARNED.value)
    assert row.earned_at is not None
    assert row.available_at is not None
    assert row.available_at - row.earned_at == timedelta(days=21)


@pytest.mark.django_db
def test_payout_blocked_while_commission_on_hold() -> None:
    _platform, _agency_id, agency_client = _ready_paid_agency()
    _verify_kyc(agency_client)
    denied = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000, "method_label": "bank ****1111"},
        HTTP_IDEMPOTENCY_KEY="po-hold",
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "payout_insufficient"


@pytest.mark.django_db
def test_platform_payout_detail_includes_compliance() -> None:
    platform, _agency_id, agency_client = _ready_paid_agency()
    payout_id = _request_payout(agency_client, key="po-detail")
    detail = platform.get(f"/api/v1/platform/payouts/{payout_id}")
    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["status"] == "requested"
    assert body["requested_at"]
    compliance = body["compliance"]
    assert compliance["agency_status"] == "active"
    assert compliance["kyc_status"] == "verified"
    assert compliance["kyc_frozen"] is False
    assert compliance["payout_eligible"] is True
    assert compliance["wallet_frozen"] is False
    queued = platform.get("/api/v1/platform/payouts?status=requested")
    assert queued.status_code == 200
    assert any(row["id"] == payout_id for row in queued.json()["data"])


@pytest.mark.django_db
def test_payout_reject_notifies_once_and_replay_does_not_duplicate_request() -> None:
    platform, _agency_id, agency_client = _ready_paid_agency()
    payout_id = _request_payout(agency_client, key="po-reject")
    replay = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000, "method_label": "bank ****1111"},
        HTTP_IDEMPOTENCY_KEY="po-reject",
    )
    assert replay.status_code == 201
    assert replay.json()["data"]["id"] == payout_id
    assert _event_count(agency_client, "/api/v1/agency/notifications", "payout.requested") == 1
    rejected = _post(
        platform, f"/api/v1/platform/payouts/{payout_id}/action", {"action": "reject"}
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "rejected"
    assert _event_count(agency_client, "/api/v1/agency/notifications", "payout.rejected") == 1


@pytest.mark.django_db
def test_mark_paid_without_proof_when_setting_disabled() -> None:
    platform, _agency_id, agency_client = _ready_paid_agency()
    payout_id = _request_payout(agency_client, key="po-noproof-ok")
    changed = _patch(
        platform,
        "/api/v1/platform/settings",
        {"key": "payout.proof_required", "value": False, "reason": "lab"},
    )
    assert changed.status_code == 200
    _post(platform, f"/api/v1/platform/payouts/{payout_id}/action", {"action": "approve"})
    paid = _post(
        platform,
        f"/api/v1/platform/payouts/{payout_id}/mark-paid",
        {"transaction_ref": "ach-2"},
    )
    assert paid.status_code == 200
    assert paid.json()["data"]["status"] == "paid"


@pytest.mark.django_db
def test_payout_request_succeeds_when_notify_fails(monkeypatch) -> None:
    _platform, _agency_id, agency_client = _ready_paid_agency()
    _verify_kyc(agency_client)
    ReleaseHolds(ledger(), tenant_repo(), _Clock(datetime.now(UTC) + timedelta(days=16))).execute()

    class Boom:
        def dispatch(self, command):
            raise RuntimeError("mail down")

    monkeypatch.setattr(
        "control_plane.notifications.application.hooks.notifications",
        lambda: Boom(),
    )
    requested = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000, "method_label": "bank ****1111"},
        HTTP_IDEMPOTENCY_KEY="po-notify-fail",
    )
    assert requested.status_code == 201
