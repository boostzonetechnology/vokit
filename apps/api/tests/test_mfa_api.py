"""MFA enrollment, login challenge, recovery, and admin reset (VKT-007 / SEC-013)."""

from __future__ import annotations

import json
import re
import uuid

import pyotp
import pytest
from django.core import mail
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import MfaChallenge, MfaMethod, User
from control_plane.platform_settings.application.ports import SettingRecord
from control_plane.platform_settings.infrastructure.repositories import DjangoSettingRepository
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"


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


def _create_user(
    email: str,
    *,
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


def _login(client: Client, email: str):
    return _post(client, "/api/v1/auth/login", {"email": email, "password": PASSWORD})


def _otp_from_mailbox() -> str:
    assert mail.outbox, "expected OTP email"
    match = re.search(r"\b(\d{6})\b", mail.outbox[-1].body)
    assert match, mail.outbox[-1].body
    return match.group(1)


@pytest.mark.django_db
def test_totp_enroll_and_login_challenge() -> None:
    user = _create_user(
        "totp-user@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    assert _login(client, user.email).status_code == 200

    enroll = _post(client, "/api/v1/auth/mfa/totp/enroll", {})
    assert enroll.status_code == 201
    secret = enroll.json()["data"]["secret"]
    method_id = enroll.json()["data"]["method_id"]
    code = pyotp.TOTP(secret).now()
    confirm = _post(
        client,
        "/api/v1/auth/mfa/totp/confirm",
        {"method_id": method_id, "code": code},
    )
    assert confirm.status_code == 200
    assert confirm.json()["data"]["status"] == "active"
    assert confirm.json()["data"]["recovery_codes"]

    client2 = _client()
    login = _login(client2, user.email)
    assert login.status_code == 200
    body = login.json()["data"]
    assert body["mfa_required"] is True
    challenge = body["challenge_token"]

    # Pre-auth must not unlock portal session APIs.
    denied = client2.get("/api/v1/auth/session")
    assert denied.status_code == 401

    verify = _post(
        client2,
        "/api/v1/auth/mfa/challenge/verify",
        {
            "challenge_token": challenge,
            "method_id": method_id,
            "code": pyotp.TOTP(secret).now(),
        },
    )
    assert verify.status_code == 200
    assert verify.json()["data"]["user"]["email"] == user.email
    ok = client2.get("/api/v1/auth/session")
    assert ok.status_code == 200


@pytest.mark.django_db
def test_email_otp_enroll_and_login() -> None:
    user = _create_user(
        "email-mfa@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    assert _login(client, user.email).status_code == 200

    enroll = _post(client, "/api/v1/auth/mfa/email/enroll", {})
    assert enroll.status_code == 201
    data = enroll.json()["data"]
    confirm = _post(
        client,
        "/api/v1/auth/mfa/email/confirm",
        {
            "method_id": data["method_id"],
            "challenge_token": data["challenge_token"],
            "code": _otp_from_mailbox(),
        },
    )
    assert confirm.status_code == 200
    recovery = confirm.json()["data"]["recovery_codes"][0]

    client2 = _client()
    login = _login(client2, user.email)
    challenge = login.json()["data"]["challenge_token"]
    method_id = login.json()["data"]["methods"][0]["id"]
    mail.outbox.clear()
    sent = _post(
        client2,
        "/api/v1/auth/mfa/challenge/send",
        {"challenge_token": challenge, "method_id": method_id},
    )
    assert sent.status_code == 200
    verify = _post(
        client2,
        "/api/v1/auth/mfa/challenge/verify",
        {
            "challenge_token": challenge,
            "method_id": method_id,
            "code": _otp_from_mailbox(),
        },
    )
    assert verify.status_code == 200

    # Recovery code path after logout.
    _post(client2, "/api/v1/auth/logout", {})
    login3 = _login(client2, user.email)
    challenge3 = login3.json()["data"]["challenge_token"]
    verify3 = _post(
        client2,
        "/api/v1/auth/mfa/challenge/verify",
        {"challenge_token": challenge3, "recovery_code": recovery},
    )
    assert verify3.status_code == 200


@pytest.mark.django_db
def test_cannot_disable_last_method_when_privileged_required() -> None:
    user = _create_user(
        "priv-mfa@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin"
    )
    DjangoSettingRepository().upsert(
        SettingRecord(
            key="security.mfa_required_privileged",
            value=True,
            secret=False,
            updated_by_id=None,
        )
    )
    client = _client()
    # Flag on + no enrollment → login blocked (existing behavior).
    denied = _login(client, user.email)
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "mfa_required"

    DjangoSettingRepository().upsert(
        SettingRecord(
            key="security.mfa_required_privileged",
            value=False,
            secret=False,
            updated_by_id=None,
        )
    )
    assert _login(client, user.email).status_code == 200
    enroll = _post(client, "/api/v1/auth/mfa/totp/enroll", {})
    secret = enroll.json()["data"]["secret"]
    method_id = enroll.json()["data"]["method_id"]
    confirm = _post(
        client,
        "/api/v1/auth/mfa/totp/confirm",
        {"method_id": method_id, "code": pyotp.TOTP(secret).now()},
    )
    recovery = confirm.json()["data"]["recovery_codes"][0]

    DjangoSettingRepository().upsert(
        SettingRecord(
            key="security.mfa_required_privileged",
            value=True,
            secret=False,
            updated_by_id=None,
        )
    )
    # Re-login with MFA.
    client2 = _client()
    login = _login(client2, user.email)
    challenge = login.json()["data"]["challenge_token"]
    _post(
        client2,
        "/api/v1/auth/mfa/challenge/verify",
        {
            "challenge_token": challenge,
            "method_id": method_id,
            "code": pyotp.TOTP(secret).now(),
        },
    )
    blocked = _post(
        client2,
        f"/api/v1/auth/mfa/methods/{method_id}/disable",
        {"recovery_code": recovery},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "mfa_last_method"


@pytest.mark.django_db
def test_admin_mfa_reset_requires_reason() -> None:
    admin = _create_user(
        "reset-admin@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin"
    )
    target = _create_user(
        "reset-target@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    assert _login(client, admin.email).status_code == 200
    # Seed an active method on target via service layer path through enroll as target.
    target_client = _client()
    assert _login(target_client, target.email).status_code == 200
    enroll = _post(target_client, "/api/v1/auth/mfa/totp/enroll", {})
    secret = enroll.json()["data"]["secret"]
    method_id = enroll.json()["data"]["method_id"]
    _post(
        target_client,
        "/api/v1/auth/mfa/totp/confirm",
        {"method_id": method_id, "code": pyotp.TOTP(secret).now()},
    )
    assert MfaMethod.objects.filter(user=target, status="active").exists()

    missing = _post(client, f"/api/v1/platform/users/{target.id}/mfa/reset", {})
    assert missing.status_code == 400
    reset = _post(
        client,
        f"/api/v1/platform/users/{target.id}/mfa/reset",
        {"reason": "lost authenticator"},
    )
    assert reset.status_code == 200
    assert not MfaMethod.objects.filter(user=target, status="active").exists()


@pytest.mark.django_db
def test_replay_otp_rejected() -> None:
    user = _create_user(
        "replay@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    assert _login(client, user.email).status_code == 200
    enroll = _post(client, "/api/v1/auth/mfa/email/enroll", {})
    data = enroll.json()["data"]
    code = _otp_from_mailbox()
    assert (
        _post(
            client,
            "/api/v1/auth/mfa/email/confirm",
            {
                "method_id": data["method_id"],
                "challenge_token": data["challenge_token"],
                "code": code,
            },
        ).status_code
        == 200
    )
    # Enroll challenge consumed — replay fails.
    again = _post(
        client,
        "/api/v1/auth/mfa/email/confirm",
        {
            "method_id": data["method_id"],
            "challenge_token": data["challenge_token"],
            "code": code,
        },
    )
    assert again.status_code in {400, 401}
    assert MfaChallenge.objects.filter(token_hash__isnull=False).exists()


@pytest.mark.django_db
def test_mfa_challenge_send_rate_limited(monkeypatch) -> None:
    from control_plane.identity.infrastructure.rate_limit import CacheKeyedRateLimiter
    import control_plane.identity.api.mfa_views as mfa_views

    user = _create_user(
        "send-rl@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    assert _login(client, user.email).status_code == 200
    # Enroll via email before tightening the send limiter.
    enroll = _post(client, "/api/v1/auth/mfa/email/enroll", {})
    data = enroll.json()["data"]
    _post(
        client,
        "/api/v1/auth/mfa/email/confirm",
        {
            "method_id": data["method_id"],
            "challenge_token": data["challenge_token"],
            "code": _otp_from_mailbox(),
        },
    )
    monkeypatch.setattr(
        mfa_views,
        "mfa_send_limiter",
        lambda: CacheKeyedRateLimiter(prefix="test.mfa.send", limit=2, window_seconds=300),
    )
    client2 = _client()
    login = _login(client2, user.email)
    challenge = login.json()["data"]["challenge_token"]
    method_id = login.json()["data"]["methods"][0]["id"]
    assert (
        _post(
            client2,
            "/api/v1/auth/mfa/challenge/send",
            {"challenge_token": challenge, "method_id": method_id},
        ).status_code
        == 200
    )
    assert (
        _post(
            client2,
            "/api/v1/auth/mfa/challenge/send",
            {"challenge_token": challenge, "method_id": method_id},
        ).status_code
        == 200
    )
    blocked = _post(
        client2,
        "/api/v1/auth/mfa/challenge/send",
        {"challenge_token": challenge, "method_id": method_id},
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"


@pytest.mark.django_db
def test_mfa_challenge_verify_rate_limited(monkeypatch) -> None:
    from control_plane.identity.infrastructure.rate_limit import CacheKeyedRateLimiter
    import control_plane.identity.api.mfa_views as mfa_views

    monkeypatch.setattr(
        mfa_views,
        "mfa_verify_limiter",
        lambda: CacheKeyedRateLimiter(prefix="test.mfa.verify", limit=3, window_seconds=300),
    )
    user = _create_user(
        "verify-rl@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    assert _login(client, user.email).status_code == 200
    enroll = _post(client, "/api/v1/auth/mfa/totp/enroll", {})
    secret = enroll.json()["data"]["secret"]
    method_id = enroll.json()["data"]["method_id"]
    _post(
        client,
        "/api/v1/auth/mfa/totp/confirm",
        {"method_id": method_id, "code": pyotp.TOTP(secret).now()},
    )
    client2 = _client()
    login = _login(client2, user.email)
    challenge = login.json()["data"]["challenge_token"]
    for _ in range(3):
        bad = _post(
            client2,
            "/api/v1/auth/mfa/challenge/verify",
            {
                "challenge_token": challenge,
                "method_id": method_id,
                "code": "000000",
            },
        )
        assert bad.status_code == 401
    blocked = _post(
        client2,
        "/api/v1/auth/mfa/challenge/verify",
        {
            "challenge_token": challenge,
            "method_id": method_id,
            "code": "000000",
        },
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"


@pytest.mark.django_db
def test_mfa_challenge_send_rate_limited(monkeypatch) -> None:
    from control_plane.identity.infrastructure.rate_limit import CacheKeyedRateLimiter
    import control_plane.identity.api.mfa_views as mfa_views

    monkeypatch.setattr(
        mfa_views,
        "mfa_send_limiter",
        lambda: CacheKeyedRateLimiter(prefix="test.mfa.send", limit=2, window_seconds=300),
    )
    user = _create_user(
        "send-rl@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    assert _login(client, user.email).status_code == 200
    enroll = _post(client, "/api/v1/auth/mfa/email/enroll", {})
    data = enroll.json()["data"]
    _post(
        client,
        "/api/v1/auth/mfa/email/confirm",
        {
            "method_id": data["method_id"],
            "challenge_token": data["challenge_token"],
            "code": _otp_from_mailbox(),
        },
    )
    client2 = _client()
    login = _login(client2, user.email)
    challenge = login.json()["data"]["challenge_token"]
    method_id = login.json()["data"]["methods"][0]["id"]
    assert (
        _post(
            client2,
            "/api/v1/auth/mfa/challenge/send",
            {"challenge_token": challenge, "method_id": method_id},
        ).status_code
        == 200
    )
    assert (
        _post(
            client2,
            "/api/v1/auth/mfa/challenge/send",
            {"challenge_token": challenge, "method_id": method_id},
        ).status_code
        == 200
    )
    blocked = _post(
        client2,
        "/api/v1/auth/mfa/challenge/send",
        {"challenge_token": challenge, "method_id": method_id},
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"


@pytest.mark.django_db
def test_mfa_challenge_verify_rate_limited(monkeypatch) -> None:
    from control_plane.identity.infrastructure.rate_limit import CacheKeyedRateLimiter
    import control_plane.identity.api.mfa_views as mfa_views

    monkeypatch.setattr(
        mfa_views,
        "mfa_verify_limiter",
        lambda: CacheKeyedRateLimiter(prefix="test.mfa.verify", limit=3, window_seconds=300),
    )
    user = _create_user(
        "verify-rl@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    assert _login(client, user.email).status_code == 200
    enroll = _post(client, "/api/v1/auth/mfa/totp/enroll", {})
    secret = enroll.json()["data"]["secret"]
    method_id = enroll.json()["data"]["method_id"]
    _post(
        client,
        "/api/v1/auth/mfa/totp/confirm",
        {"method_id": method_id, "code": pyotp.TOTP(secret).now()},
    )
    client2 = _client()
    login = _login(client2, user.email)
    challenge = login.json()["data"]["challenge_token"]
    for _ in range(3):
        bad = _post(
            client2,
            "/api/v1/auth/mfa/challenge/verify",
            {
                "challenge_token": challenge,
                "method_id": method_id,
                "code": "000000",
            },
        )
        assert bad.status_code == 401
    blocked = _post(
        client2,
        "/api/v1/auth/mfa/challenge/verify",
        {
            "challenge_token": challenge,
            "method_id": method_id,
            "code": "000000",
        },
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
