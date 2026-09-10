from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.tenancy.domain.types import MigrationJobStatus
from control_plane.tenancy.infrastructure.container import (
    backup_tenant,
    isolation_records,
    migration_batch,
    restore_tenant,
)
from shared_kernel.hmac import sign_hmac_sha256
from shared_kernel.ids import new_uuid7
from tenant.schema import CURRENT_VERSION

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


def _user(email: str, principal: PrincipalType, role: str, tenant_id=None, customer_id=None):
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


def _agency(platform: Client, name: str, db_name: str, owner: str):
    _ = db_name
    return _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": name,
            "legal_name": name,
            "owner_email": owner,
        },
    )


@pytest.mark.django_db
def test_staging_sandbox_canary_payment_and_restore() -> None:
    _user("platform-stage@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform-stage@vokit.test")
    one = _agency(platform, "Stage A", "stage_a", "oa-stage@vokit.test")
    two = _agency(platform, "Stage B", "stage_b", "ob-stage@vokit.test")
    assert one.status_code == 201
    agency_a = uuid.UUID(one.json()["data"]["id"])
    agency_b = uuid.UUID(two.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Stage Cust", "agency_id": str(agency_a)},
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": "Stage",
            "price_minor": 5000,
            "included_minutes": 50,
            "allow_topups": False,
            "topup_minutes": 0,
            "topup_price_minor": 0,
            "overage_enabled": False,
            "overage_price_per_minute_minor": 0,
            "grace_seconds": 30,
        },
    )
    version_id = plan.json()["data"]["versions"][0]["id"]
    assigned = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": version_id},
    )
    invoice_id = assigned.json()["data"]["id"]
    amount = assigned.json()["data"]["total_minor"]
    _user("agency-stage-a@vokit.test", PrincipalType.AGENCY, "agency_owner", agency_a)
    _user("agency-stage-b@vokit.test", PrincipalType.AGENCY, "agency_owner", agency_b)
    agency_a_client = _client()
    agency_b_client = _client()
    _login(agency_a_client, "agency-stage-a@vokit.test")
    _login(agency_b_client, "agency-stage-b@vokit.test")
    body = json.dumps(
        {
            "event_id": "evt_stage_1",
            "invoice_id": invoice_id,
            "amount_minor": amount,
            "currency": "USD",
            "status": "captured",
        }
    ).encode()
    captured = Client(enforce_csrf_checks=True).post(
        "/webhooks/stripe/v1/",
        data=body,
        content_type="application/json",
        HTTP_X_VOKIT_PAYMENTS_SIGNATURE=sign_hmac_sha256(
            secret_ref=STRIPE_REF, raw_body=body
        ),
    )
    assert captured.status_code == 200
    replay = Client(enforce_csrf_checks=True).post(
        "/webhooks/stripe/v1/",
        data=body,
        content_type="application/json",
        HTTP_X_VOKIT_PAYMENTS_SIGNATURE=sign_hmac_sha256(
            secret_ref=STRIPE_REF, raw_body=body
        ),
    )
    assert replay.json()["data"]["duplicate"] is True
    dash_a = agency_a_client.get("/api/v1/agency/dashboard?period=30d")
    dash_b = agency_b_client.get("/api/v1/agency/dashboard?period=30d")
    assert dash_a.status_code == 200
    kpis_a = dash_a.json()["data"]["kpis"]
    revenue = next(item["value"] for item in kpis_a if item["key"] == "customer_mrr_minor")
    assert revenue == amount
    assert next(
        item["value"] for item in dash_b.json()["data"]["kpis"] if item["key"] == "customers"
    ) == 0
    foreign = agency_b_client.get(f"/api/v1/agency/customers/{customer_id}")
    assert foreign.status_code in {403, 404}
    jobs = migration_batch().execute(
        [agency_a, agency_b],
        canary_ids=[agency_a],
        target_version=CURRENT_VERSION,
        canary_only=True,
    )
    assert len(jobs) == 1
    assert jobs[0].canary is True
    assert jobs[0].status is MigrationJobStatus.SUCCEEDED
    marker = new_uuid7()
    isolation_records().put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=agency_a,
        claimed_tenant_id=None,
        permissions=frozenset(),
        object_id=marker,
        payload="pre-restore",
    )
    snapshot = backup_tenant().execute(agency_a)
    isolation_records().put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=agency_a,
        claimed_tenant_id=None,
        permissions=frozenset(),
        object_id=marker,
        payload="post-backup-mutation",
    )
    restore_tenant().execute(agency_a, snapshot)
    restored = isolation_records().get(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=agency_a,
        claimed_tenant_id=None,
        permissions=frozenset(),
        object_id=marker,
    )
    assert restored.payload == "pre-restore"
    health = platform.get("/api/v1/health")
    assert health.status_code == 200
