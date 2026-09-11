from __future__ import annotations

import json
import uuid

import pytest
from django.db import models
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.kyc import models as kyc_models
from control_plane.kyc.infrastructure.hmac import sign_kyc_body
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"
WEBHOOK_REF = "KYC_WEBHOOK_SECRET"


def _client() -> Client:
    return Client(enforce_csrf_checks=True)


def _csrf(client: Client) -> str:
    return client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]


def _post(client: Client, path: str, payload: dict):
    return client.post(
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
) -> User:
    user = User.objects.create_user(email=email, password=PASSWORD)
    DjangoMembershipRepository().create(
        MembershipRecord(
            id=new_uuid7(),
            user_id=user.id,
            principal_type=principal,
            role=role,
            tenant_id=tenant_id,
            customer_id=None,
            status=MembershipStatus.ACTIVE,
        )
    )
    return user


def _login(client: Client, email: str) -> None:
    login = _post(
        client,
        "/api/v1/auth/login",
        {"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200


def _create_agency(client: Client, name: str, db_name: str, owner: str):
    _ = db_name
    from tests.tenant_db_fixtures import tenant_db_payload

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
        {"action": "activate"},
    )


def _webhook(payload: dict, *, signature: str | None = None):
    body = json.dumps(payload).encode()
    header = signature
    if header is None:
        header = sign_kyc_body(secret_ref=WEBHOOK_REF, raw_body=body)
    client = Client(enforce_csrf_checks=True)
    return client.post(
        "/webhooks/kyc/external/v1/",
        data=body,
        content_type="application/json",
        HTTP_X_VOKIT_KYC_SIGNATURE=header,
    )


@pytest.mark.django_db
def test_payout_rejects_unverified() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "KYC A", "kyc_a", "oa-kyc@vokit.test")
    assert agency.status_code == 200
    agency_id = agency.json()["data"]["id"]
    _user("agency-kyc@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(agency_id))
    agency_client = _client()
    _login(agency_client, "agency-kyc@vokit.test")
    denied = _post(agency_client, "/api/v1/agency/payouts", {})
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "payout_kyc_unverified"
    status = agency_client.get("/api/v1/agency/kyc")
    assert status.status_code == 200
    assert status.json()["data"]["payout_eligible"] is False


@pytest.mark.django_db
def test_signed_webhook_verifies_and_unlocks_payout() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "KYC B", "kyc_b", "ob-kyc@vokit.test")
    agency_id = agency.json()["data"]["id"]
    _user("agency-kycb@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(agency_id))
    agency_client = _client()
    _login(agency_client, "agency-kycb@vokit.test")
    session = _post(agency_client, "/api/v1/agency/kyc/session", {})
    assert session.status_code == 201
    assert "hosted_url" in session.json()["data"]
    assert "document" not in json.dumps(session.json()).lower()
    event_id = f"evt-{new_uuid7()}"
    hook = _webhook(
        {
            "event_id": event_id,
            "session_id": session.json()["data"]["session_id"],
            "status": "verified",
            "reason_code": "ok",
            "document_base64": "SHOULD_NOT_PERSIST",
        }
    )
    assert hook.status_code == 200
    assert hook.json()["data"]["duplicate"] is False
    replay = _webhook(
        {
            "event_id": event_id,
            "session_id": session.json()["data"]["session_id"],
            "status": "rejected",
        }
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["duplicate"] is True
    allowed = _post(agency_client, "/api/v1/agency/payouts", {})
    assert allowed.status_code == 400
    assert allowed.json()["error"]["code"] == "validation_error"
    events = list(kyc_models.KycProviderEvent.objects.all())
    assert len(events) == 1
    dumped = json.dumps({row.event_id: row.reason_code for row in events})
    assert "SHOULD_NOT_PERSIST" not in dumped
    assert "document_base64" not in dumped


@pytest.mark.django_db
def test_forged_webhook_is_rejected() -> None:
    hook = _webhook(
        {"event_id": "x", "session_id": "missing", "status": "verified"},
        signature="sha256=deadbeef",
    )
    assert hook.status_code == 401
    assert hook.json()["error"]["code"] == "kyc_signature_invalid"


@pytest.mark.django_db
def test_agency_cannot_mark_itself_verified() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "KYC C", "kyc_c", "oc-kyc@vokit.test")
    agency_id = agency.json()["data"]["id"]
    _user("agency-kycc@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(agency_id))
    agency_client = _client()
    _login(agency_client, "agency-kycc@vokit.test")
    forged = _post(agency_client, "/api/v1/agency/kyc", {"status": "verified"})
    assert forged.status_code == 405
    status = agency_client.get("/api/v1/agency/kyc")
    assert status.json()["data"]["status"] == "not_started"


@pytest.mark.django_db
def test_super_admin_freeze_blocks_verified_payout() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "KYC D", "kyc_d", "od-kyc@vokit.test")
    agency_id = agency.json()["data"]["id"]
    _user("agency-kycd@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(agency_id))
    agency_client = _client()
    _login(agency_client, "agency-kycd@vokit.test")
    session = _post(agency_client, "/api/v1/agency/kyc/session", {})
    _webhook(
        {
            "event_id": str(new_uuid7()),
            "session_id": session.json()["data"]["session_id"],
            "status": "verified",
        }
    )
    cases = platform.get("/api/v1/platform/kyc/cases")
    assert cases.status_code == 200
    case_id = cases.json()["data"][0]["id"]
    frozen = _post(
        platform,
        f"/api/v1/platform/kyc/cases/{case_id}/override",
        {"action": "freeze", "internal_note": "risk"},
    )
    assert frozen.status_code == 200
    assert frozen.json()["data"]["frozen"] is True
    denied = _post(agency_client, "/api/v1/agency/payouts", {})
    assert denied.status_code == 409


@pytest.mark.django_db
def test_agencies_cannot_see_each_others_kyc() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    one = _create_agency(platform, "KYC E", "kyc_e", "oe-kyc@vokit.test")
    two = _create_agency(platform, "KYC F", "kyc_f", "of-kyc@vokit.test")
    id_a = one.json()["data"]["id"]
    id_b = two.json()["data"]["id"]
    _user("agency-kyce@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(id_a))
    _user("agency-kycf@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(id_b))
    client_a = _client()
    _login(client_a, "agency-kyce@vokit.test")
    client_b = _client()
    _login(client_b, "agency-kycf@vokit.test")
    started = _post(client_a, "/api/v1/agency/kyc/session", {})
    assert started.status_code == 201
    other = client_b.get("/api/v1/agency/kyc")
    assert other.json()["data"]["status"] == "not_started"
    assert other.json()["data"].get("case") is None


@pytest.mark.django_db
def test_kyc_models_do_not_store_files() -> None:
    forbidden = (models.FileField, models.BinaryField, models.ImageField)
    for model in (kyc_models.KycCase, kyc_models.KycSettings, kyc_models.KycProviderEvent):
        for field in model._meta.get_fields():
            assert not isinstance(field, forbidden)


@pytest.mark.django_db
def test_settings_store_secret_refs_only() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    saved = _post(
        platform,
        "/api/v1/platform/kyc/settings",
        {
            "api_key_ref": "KYC_API_KEY",
            "webhook_secret_ref": "KYC_WEBHOOK_SECRET",
            "hosted_base_url": "https://kyc.example.test",
        },
    )
    assert saved.status_code == 200
    body = json.dumps(saved.json())
    assert "test-kyc-key" not in body
    assert "test-kyc-webhook" not in body
    assert saved.json()["data"]["api_key_ref"] == "KYC_API_KEY"


@pytest.mark.django_db
@pytest.mark.django_db
def test_no_kyc_document_upload_route() -> None:
    client = _client()
    response = client.post("/api/v1/agency/kyc/documents")
    assert response.status_code == 404


@pytest.mark.django_db
def test_support_admin_cannot_review_kyc() -> None:
    _user("support@vokit.test", PrincipalType.PLATFORM, "support_admin")
    client = _client()
    _login(client, "support@vokit.test")
    listed = client.get("/api/v1/platform/kyc/cases")
    assert listed.status_code == 403
