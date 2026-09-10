from __future__ import annotations

import json
import uuid

import pytest
from django.db import IntegrityError
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.demo import DEMO_AGENCY_TENANT_ID, DEMO_CUSTOMER_ID
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import Invitation, Membership, User, UserSession
from control_plane.platform_settings.application.ports import SettingRecord
from control_plane.platform_settings.infrastructure.repositories import (
    DjangoSettingRepository,
)
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"


def _client() -> Client:
    return Client(enforce_csrf_checks=True)


def _csrf(client: Client) -> str:
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    return response.json()["data"]["csrf_token"]


def _post(client: Client, path: str, payload: dict, csrf: str | None = None):
    token = csrf or _csrf(client)
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )


def _create_user(
    email: str,
    *,
    principal: PrincipalType,
    role: str,
    tenant_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
    password: str = PASSWORD,
) -> User:
    user = User.objects.create_user(email=email, password=password)
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


@pytest.mark.django_db
def test_email_unique_at_storage() -> None:
    User.objects.create_user(email="same@vokit.test", password=PASSWORD)
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="same@vokit.test", password=PASSWORD)


@pytest.mark.django_db
def test_user_cannot_hold_platform_and_tenant_membership() -> None:
    user = _create_user("only-one@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    with pytest.raises(IntegrityError):
        Membership.objects.create(
            user=user,
            principal_type="agency",
            role="agency_owner",
            tenant_id=DEMO_AGENCY_TENANT_ID,
            status="active",
        )


@pytest.mark.django_db
def test_login_logout_and_session() -> None:
    _create_user("platform@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    client = _client()
    login = _post(
        client,
        "/api/v1/auth/login",
        {"email": "platform@vokit.test", "password": PASSWORD},
    )
    assert login.status_code == 200
    body = login.json()["data"]
    assert body["membership"]["principal_type"] == "platform"
    assert "users.invite" in body["permissions"]
    session = client.get("/api/v1/auth/session")
    assert session.status_code == 200
    logout = _post(client, "/api/v1/auth/logout", {})
    assert logout.status_code == 200
    denied = client.get("/api/v1/auth/session")
    assert denied.status_code == 401
    assert denied.json()["error"]["code"] == "unauthenticated"


@pytest.mark.django_db
def test_login_failure_is_generic() -> None:
    client = _client()
    response = _post(
        client,
        "/api/v1/auth/login",
        {"email": "missing@vokit.test", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password."


@pytest.mark.django_db
def test_csrf_required_on_login() -> None:
    _create_user("platform@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    client = _client()
    client.get("/api/v1/auth/csrf")
    response = client.post(
        "/api/v1/auth/login",
        data=json.dumps({"email": "platform@vokit.test", "password": PASSWORD}),
        content_type="application/json",
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_denied"


@pytest.mark.django_db
def test_wrong_portal_is_403() -> None:
    _create_user(
        "agency@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_owner",
        tenant_id=DEMO_AGENCY_TENANT_ID,
    )
    client = _client()
    login = _post(
        client,
        "/api/v1/auth/login",
        {"email": "agency@vokit.test", "password": PASSWORD},
    )
    assert login.status_code == 200
    forbidden = client.get("/api/v1/platform/me")
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "forbidden"
    allowed = client.get("/api/v1/agency/me")
    assert allowed.status_code == 200
    assert allowed.json()["data"]["membership"]["tenant_id"] == str(DEMO_AGENCY_TENANT_ID)


@pytest.mark.django_db
def test_forged_tenant_id_cannot_change_session_or_invite_scope() -> None:
    agency = _create_user(
        "agency@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_owner",
        tenant_id=DEMO_AGENCY_TENANT_ID,
    )
    client = _client()
    forged = uuid.UUID("0199bbbb-0000-7000-8000-000000000099")
    login = _post(
        client,
        "/api/v1/auth/login",
        {
            "email": "agency@vokit.test",
            "password": PASSWORD,
            "tenant_id": str(forged),
            "role": "super_admin",
            "permissions": ["kyc.review"],
        },
    )
    assert login.status_code == 200
    membership = login.json()["data"]["membership"]
    assert membership["tenant_id"] == str(DEMO_AGENCY_TENANT_ID)
    assert membership["role"] == "agency_owner"
    assert "kyc.review" not in login.json()["data"]["permissions"]

    invite = _post(
        client,
        "/api/v1/agency/team",
        {"email": "new-agent@vokit.test", "role": "agency_admin", "tenant_id": str(forged)},
    )
    assert invite.status_code == 201
    assert invite.json()["data"]["tenant_id"] == str(DEMO_AGENCY_TENANT_ID)
    row = Invitation.objects.get(email="new-agent@vokit.test")
    assert row.tenant_id == DEMO_AGENCY_TENANT_ID
    assert row.invited_by_id == agency.id


@pytest.mark.django_db
def test_agency_cannot_grant_platform_permissions() -> None:
    _create_user(
        "agency@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_owner",
        tenant_id=DEMO_AGENCY_TENANT_ID,
    )
    client = _client()
    _post(client, "/api/v1/auth/login", {"email": "agency@vokit.test", "password": PASSWORD})
    response = _post(
        client,
        "/api/v1/agency/team",
        {"email": "evil@vokit.test", "role": "super_admin"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_role"


@pytest.mark.django_db
def test_invite_accept_lifecycle() -> None:
    _create_user("platform@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    client = _client()
    _post(client, "/api/v1/auth/login", {"email": "platform@vokit.test", "password": PASSWORD})
    invited = _post(
        client,
        "/api/v1/platform/invitations",
        {
            "email": "customer@vokit.test",
            "principal_type": "customer",
            "role": "customer_owner",
            "tenant_id": str(DEMO_AGENCY_TENANT_ID),
            "customer_id": str(DEMO_CUSTOMER_ID),
        },
    )
    assert invited.status_code == 201
    token = invited.json()["data"]["token"]

    guest = _client()
    accepted = _post(
        guest,
        "/api/v1/auth/invitations/accept",
        {"token": token, "password": PASSWORD},
    )
    assert accepted.status_code == 201
    login = _post(
        guest,
        "/api/v1/auth/login",
        {"email": "customer@vokit.test", "password": PASSWORD},
    )
    assert login.status_code == 200
    assert login.json()["data"]["membership"]["principal_type"] == "customer"
    me = guest.get("/api/v1/customer/me")
    assert me.status_code == 200


@pytest.mark.django_db
def test_invite_existing_member_conflicts() -> None:
    _create_user("platform@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    _create_user(
        "agency@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_owner",
        tenant_id=DEMO_AGENCY_TENANT_ID,
    )
    client = _client()
    _post(client, "/api/v1/auth/login", {"email": "platform@vokit.test", "password": PASSWORD})
    response = _post(
        client,
        "/api/v1/platform/invitations",
        {"email": "agency@vokit.test", "principal_type": "platform", "role": "support_admin"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "membership_conflict"


@pytest.mark.django_db
def test_disable_revokes_sessions() -> None:
    admin = _create_user(
        "platform@vokit.test",
        principal=PrincipalType.PLATFORM,
        role="super_admin",
    )
    target = _create_user(
        "agency@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_owner",
        tenant_id=DEMO_AGENCY_TENANT_ID,
    )
    tenant_client = _client()
    logged_in = _post(
        tenant_client,
        "/api/v1/auth/login",
        {"email": "agency@vokit.test", "password": PASSWORD},
    )
    assert logged_in.status_code == 200
    assert tenant_client.get("/api/v1/agency/me").status_code == 200
    assert UserSession.objects.filter(user=target).exists()

    admin_client = _client()
    _post(
        admin_client,
        "/api/v1/auth/login",
        {"email": "platform@vokit.test", "password": PASSWORD},
    )
    disabled = _post(admin_client, f"/api/v1/platform/users/{target.id}/disable", {})
    assert disabled.status_code == 200
    assert disabled.json()["data"]["sessions_revoked"] >= 1
    assert tenant_client.get("/api/v1/agency/me").status_code == 401
    relogin = _post(
        tenant_client,
        "/api/v1/auth/login",
        {"email": "agency@vokit.test", "password": PASSWORD},
    )
    assert relogin.status_code == 401
    assert not UserSession.objects.filter(user=target).exists()

    self_disable = _post(admin_client, f"/api/v1/platform/users/{admin.id}/disable", {})
    assert self_disable.status_code == 400


@pytest.mark.django_db
def test_login_cycles_session_and_rate_limits() -> None:
    _create_user("rate@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    client = _client()
    client.get("/api/v1/auth/csrf")
    client.session.save()
    before = client.session.session_key
    assert before
    login = _post(client, "/api/v1/auth/login", {"email": "rate@vokit.test", "password": PASSWORD})
    assert login.status_code == 200
    after = client.session.session_key
    assert after
    assert after != before
    attacker = _client()
    last = None
    for _ in range(8):
        last = _post(
            attacker,
            "/api/v1/auth/login",
            {"email": "rate@vokit.test", "password": "wrong-password"},
        )
        assert last.status_code == 401
    blocked = _post(
        attacker,
        "/api/v1/auth/login",
        {"email": "rate@vokit.test", "password": "wrong-password"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"


@pytest.mark.django_db
def test_privileged_mfa_setting_blocks_login_without_enrollment() -> None:
    _create_user("mfa-admin@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    _create_user(
        "mfa-cust@vokit.test",
        principal=PrincipalType.CUSTOMER,
        role="customer_owner",
        tenant_id=DEMO_AGENCY_TENANT_ID,
        customer_id=DEMO_CUSTOMER_ID,
    )
    DjangoSettingRepository().upsert(
        SettingRecord(
            key="security.mfa_required_privileged",
            value=True,
            secret=False,
            updated_by_id=None,
        )
    )
    admin = _client()
    denied = _post(
        admin,
        "/api/v1/auth/login",
        {"email": "mfa-admin@vokit.test", "password": PASSWORD},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "mfa_required"
    customer = _client()
    allowed = _post(
        customer,
        "/api/v1/auth/login",
        {"email": "mfa-cust@vokit.test", "password": PASSWORD},
    )
    assert allowed.status_code == 200
