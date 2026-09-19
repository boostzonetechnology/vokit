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

    shared = _patch(platform, f"/api/v1/platform/payouts/{payout_id}/proof", {"agency_visible": True})
    assert shared.status_code == 200
    assert shared.json()["data"]["agency_visible"] is True
    visible = agency_client.get(f"/api/v1/agency/payouts/{payout_id}/proof")
    assert visible.status_code == 200
    proof_data = visible.json()["data"]
    assert proof_data["object_ref"].endswith("/proof/a")
    assert "uploaded_by_id" not in proof_data
    assert proof_data["agency_visible"] is True

    unshared = _patch(
        platform, f"/api/v1/platform/payouts/{payout_id}/proof", {"agency_visible": False}
    )
    assert unshared.status_code == 200
    assert unshared.json()["data"]["agency_visible"] is False
    denied_again = agency_client.get(f"/api/v1/agency/payouts/{payout_id}/proof")
    assert denied_again.status_code == 404

    _post(platform, f"/api/v1/platform/payouts/{payout_id}/action", {"action": "approve"})
    _patch(platform, f"/api/v1/platform/payouts/{payout_id}/proof", {"agency_visible": True})
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
    still_shared = agency_client.get(f"/api/v1/agency/payouts/{payout_id}/proof")
    assert still_shared.status_code == 200


@pytest.mark.django_db
def test_platform_can_upload_proof_image_file() -> None:
    platform, _agency_id, agency_client = _ready_paid_agency()
    _verify_kyc(agency_client)
    ReleaseHolds(ledger(), tenant_repo(), _Clock(datetime.now(UTC) + timedelta(days=16))).execute()
    requested = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000, "method_label": "bank ****1111"},
        HTTP_IDEMPOTENCY_KEY="po-file-1",
    )
    assert requested.status_code == 201
    payout_id = requested.json()["data"]["id"]
    # minimal valid PNG
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    from django.core.files.uploadedfile import SimpleUploadedFile

    uploaded = platform.post(
        f"/api/v1/platform/payouts/{payout_id}/proof",
        data={
            "agency_visible": "true",
            "file": SimpleUploadedFile("slip.png", png, content_type="image/png"),
        },
        HTTP_X_CSRFTOKEN=_csrf(platform),
    )
    assert uploaded.status_code == 201, uploaded.json()
    assert uploaded.json()["data"]["content_type"] == "image/png"
    assert uploaded.json()["data"]["agency_visible"] is True
    file_resp = agency_client.get(f"/api/v1/agency/payouts/{payout_id}/proof/file")
    assert file_resp.status_code == 200
    assert file_resp["Content-Type"].startswith("image/png")


@pytest.mark.django_db
def test_agency_cannot_fetch_foreign_shared_payout_proof() -> None:
    platform, _agency_a, agency_a = _ready_paid_agency()
    other = _create_agency(platform, "Comm B", "comm_b", "oa-comm-b@vokit.test")
    assert other.status_code == 200
    agency_b_id = uuid.UUID(other.json()["data"]["id"])
    _user(
        "agency-comm-b@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_b_id,
    )
    agency_b = _client()
    _login(agency_b, "agency-comm-b@vokit.test")
    _verify_kyc(agency_a)
    ReleaseHolds(ledger(), tenant_repo(), _Clock(datetime.now(UTC) + timedelta(days=16))).execute()
    requested = _post(
        agency_a,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000, "method_label": "bank ****1111"},
        HTTP_IDEMPOTENCY_KEY="po-share-foreign",
    )
    assert requested.status_code == 201
    payout_id = requested.json()["data"]["id"]
    assert (
        _post(
            platform,
            f"/api/v1/platform/payouts/{payout_id}/proof",
            {
                "object_ref": f"payout/{payout_id}/proof/x",
                "content_type": "application/pdf",
                "checksum": "sha256:xyz",
            },
        ).status_code
        == 201
    )
    assert (
        _patch(
            platform, f"/api/v1/platform/payouts/{payout_id}/proof", {"agency_visible": True}
        ).status_code
        == 200
    )
    denied = agency_b.get(f"/api/v1/agency/payouts/{payout_id}/proof")
    assert denied.status_code == 404
    assert "object_ref" not in json.dumps(denied.json())


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


@pytest.mark.django_db
def test_agency_payout_methods_crud_and_withdraw_dropdown() -> None:
    _platform, _agency_id, agency_client = _ready_paid_agency()
    created = _post(
        agency_client,
        "/api/v1/agency/payout-methods",
        {
            "beneficiary_name": "Acme Agency LLC",
            "account_identifier": "PK12HABB000123456789",
            "bank_name": "HBL",
            "country": "PK",
            "currency": "USD",
            "is_default": True,
        },
    )
    assert created.status_code == 201
    assert created.json()["data"]["status"] == "pending"
    assert created.json()["data"]["account_identifier_masked"].endswith("6789")
    assert "PK12" not in created.json()["data"]["account_identifier_masked"]

    _verify_kyc(agency_client)
    usable = _post(
        agency_client,
        "/api/v1/agency/payout-methods",
        {
            "beneficiary_name": "Acme Agency LLC",
            "account_identifier": "123456789012",
            "bank_name": "Meezan",
            "country": "pk",
            "is_default": True,
        },
    )
    assert usable.status_code == 201
    method_id = usable.json()["data"]["id"]
    assert usable.json()["data"]["status"] == "usable"
    assert usable.json()["data"]["label"].startswith("Meezan")

    listed = agency_client.get("/api/v1/agency/payout-methods?usable=true")
    assert listed.status_code == 200
    assert any(row["id"] == method_id for row in listed.json()["data"])

    ReleaseHolds(ledger(), tenant_repo(), _Clock(datetime.now(UTC) + timedelta(days=16))).execute()
    requested = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 3000, "payout_method_id": method_id},
        HTTP_IDEMPOTENCY_KEY="po-method-1",
    )
    assert requested.status_code == 201
    assert "Meezan" in requested.json()["data"]["method_label"]

    foreign = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 1, "payout_method_id": str(uuid.uuid4())},
        HTTP_IDEMPOTENCY_KEY="po-method-x",
    )
    assert foreign.status_code == 404

    disabled = agency_client.delete(
        f"/api/v1/agency/payout-methods/{method_id}",
        HTTP_X_CSRFTOKEN=_csrf(agency_client),
    )
    assert disabled.status_code == 200
    assert disabled.json()["data"]["status"] == "disabled"
    still_listed = agency_client.get("/api/v1/agency/payout-methods")
    assert still_listed.status_code == 200
    assert any(
        row["id"] == method_id and row["status"] == "disabled"
        for row in still_listed.json()["data"]
    )
    blocked = _post(
        agency_client,
        "/api/v1/agency/payouts",
        {"amount_minor": 1, "payout_method_id": method_id},
        HTTP_IDEMPOTENCY_KEY="po-method-disabled",
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "payout_method_unusable"

    enabled = _post(
        agency_client,
        f"/api/v1/agency/payout-methods/{method_id}",
        {"action": "enable"},
    )
    assert enabled.status_code == 200
    assert enabled.json()["data"]["status"] == "usable"
    usable_again = agency_client.get("/api/v1/agency/payout-methods?usable=true")
    assert any(row["id"] == method_id for row in usable_again.json()["data"])
