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


def _agency(platform: Client, name: str, db_name: str, owner: str):
    _ = db_name
    from tests.tenant_db_fixtures import tenant_db_payload

    return _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": name,
            "legal_name": name,
            "owner_email": owner,
            "database": tenant_db_payload(owner),
        },
    )


def _kpi(body: dict, key: str):
    return next(item for item in body["kpis"] if item["key"] == key)


@pytest.mark.django_db
def test_dashboards_are_portal_scoped_and_use_ledger_revenue() -> None:
    _user("platform-dash@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform-dash@vokit.test")
    one = _agency(platform, "Dash A", "dash_a", "oa-dash@vokit.test")
    two = _agency(platform, "Dash B", "dash_b", "ob-dash@vokit.test")
    agency_a = uuid.UUID(one.json()["data"]["id"])
    agency_b = uuid.UUID(two.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Dash Cust", "agency_id": str(agency_a)},
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": "Dash",
            "price_minor": 10000,
            "included_minutes": 100,
            "allow_topups": True,
            "topup_minutes": 50,
            "topup_price_minor": 2000,
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
    _user(
        "cust-dash@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        agency_a,
        customer_id,
    )
    _user("agency-a-dash@vokit.test", PrincipalType.AGENCY, "agency_owner", agency_a)
    _user("agency-b-dash@vokit.test", PrincipalType.AGENCY, "agency_owner", agency_b)
    customer_client = _client()
    agency_a_client = _client()
    agency_b_client = _client()
    _login(customer_client, "cust-dash@vokit.test")
    _login(agency_a_client, "agency-a-dash@vokit.test")
    _login(agency_b_client, "agency-b-dash@vokit.test")
    body = json.dumps(
        {
            "event_id": "evt_dash_1",
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
    platform_dash = platform.get("/api/v1/platform/dashboard?period=30d&timezone=UTC")
    assert platform_dash.status_code == 200
    pdata = platform_dash.json()["data"]
    assert pdata["source"] == "control_plane_projections"
    assert pdata["financial"]["gross_revenue_minor"] == amount
    assert _kpi(pdata, "customers")["value"] == 1
    filtered_b = platform.get(
        f"/api/v1/platform/dashboard?period=30d&agency_id={agency_b}"
    )
    assert _kpi(filtered_b.json()["data"], "customers")["value"] == 0
    assert filtered_b.json()["data"]["financial"]["gross_revenue_minor"] == 0
    assert agency_a_client.get("/api/v1/platform/dashboard").status_code == 403
    assert customer_client.get("/api/v1/agency/dashboard").status_code == 403
    agency_a_dash = agency_a_client.get("/api/v1/agency/dashboard?period=30d")
    agency_b_dash = agency_b_client.get("/api/v1/agency/dashboard?period=30d")
    assert agency_a_dash.status_code == 200
    assert _kpi(agency_a_dash.json()["data"], "customers")["value"] == 1
    assert agency_a_dash.json()["data"]["kpis"]
    assert _kpi(agency_a_dash.json()["data"], "customer_mrr_minor")["value"] == amount
    assert _kpi(agency_b_dash.json()["data"], "customers")["value"] == 0
    customer_dash = customer_client.get("/api/v1/customer/dashboard?period=30d")
    assert customer_dash.status_code == 200
    assert _kpi(customer_dash.json()["data"], "open_invoices")["value"] == 0
    assert _kpi(customer_dash.json()["data"], "plan")["value"] == "Dash"
    assert customer_dash.json()["data"]["alerts"]["payment_due"] is False
    custom_empty = platform.get(
        "/api/v1/platform/dashboard?period=custom"
        "&since=2026-01-01T00:00:00Z&until=2026-01-02T00:00:00Z"
        "&timezone=UTC"
    )
    assert custom_empty.status_code == 200
    assert custom_empty.json()["data"]["financial"]["gross_revenue_minor"] == 0
    custom_now = platform.get(
        "/api/v1/platform/dashboard?period=custom"
        "&since=2020-01-01T00:00:00Z&until=2099-01-01T00:00:00Z"
        "&timezone=UTC"
    )
    assert custom_now.json()["data"]["financial"]["gross_revenue_minor"] == amount
    bad_tz = platform.get("/api/v1/platform/dashboard?period=30d&timezone=Not/AZone")
    assert bad_tz.status_code == 400
