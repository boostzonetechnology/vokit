from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
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


def _login(client: Client, email: str):
    login = _post(
        client,
        "/api/v1/auth/login",
        {"email": email, "password": PASSWORD},
    )
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
            "commission_rate_bps": 1200,
        },
    )


@pytest.mark.django_db
def test_platform_creates_agency_and_customer_under_that_agency() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    agency = _create_agency(client, "North", "life_north", "owner-n@vokit.test")
    assert agency.status_code == 201
    assert agency.json()["data"]["status"] == "active"
    assert "password" not in json.dumps(agency.json())
    agency_id = agency.json()["data"]["id"]
    created = _post(
        client,
        "/api/v1/platform/customers",
        {"display_name": "Cust N", "agency_id": agency_id},
    )
    assert created.status_code == 201
    assert created.json()["data"]["agency_id"] == agency_id
    listed = client.get(f"/api/v1/platform/customers?agency_id={agency_id}")
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1


@pytest.mark.django_db
def test_two_agencies_cannot_see_each_others_customers() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency_a = _create_agency(platform, "A", "life_iso_a", "oa@vokit.test")
    agency_b = _create_agency(platform, "B", "life_iso_b", "ob@vokit.test")
    id_a = agency_a.json()["data"]["id"]
    id_b = agency_b.json()["data"]["id"]
    cust_a = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Secret A", "agency_id": id_a},
    )
    cust_b = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Secret B", "agency_id": id_b},
    )
    assert cust_a.status_code == 201
    assert cust_b.status_code == 201
    cid_a = cust_a.json()["data"]["id"]
    cid_b = cust_b.json()["data"]["id"]

    _user("agency-a@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(id_a))
    _user("agency-b@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(id_b))
    client_a = _client()
    _login(client_a, "agency-a@vokit.test")
    listed_a = client_a.get(f"/api/v1/agency/customers?tenant_id={id_b}")
    assert listed_a.status_code == 200
    names = {row["display_name"] for row in listed_a.json()["data"]}
    assert names == {"Secret A"}
    assert listed_a.json()["data"][0]["id"] == cid_a
    foreign = client_a.get(f"/api/v1/agency/customers/{cid_b}")
    assert foreign.status_code == 404
    forged_write = _post(
        client_a,
        "/api/v1/agency/customers",
        {"display_name": "Injected", "agency_id": id_b, "tenant_id": id_b},
    )
    assert forged_write.status_code == 201
    assert forged_write.json()["data"]["agency_id"] == id_a

    client_b = _client()
    _login(client_b, "agency-b@vokit.test")
    listed_b = client_b.get("/api/v1/agency/customers")
    names_b = {row["display_name"] for row in listed_b.json()["data"]}
    assert names_b == {"Secret B"}
    assert listed_b.json()["data"][0]["id"] == cid_b


@pytest.mark.django_db
def test_suspended_agency_cannot_create_customer() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Hold", "life_hold", "oh@vokit.test")
    agency_id = agency.json()["data"]["id"]
    status = _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "suspend"},
    )
    assert status.status_code == 200
    assert status.json()["data"]["status"] == "suspended"
    assert status.json()["data"]["capabilities"]["create_customers"] is False
    denied = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Nope", "agency_id": agency_id},
    )
    assert denied.status_code == 409
    _user("agency-h@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(agency_id))
    agency_client = _client()
    _login(agency_client, "agency-h@vokit.test")
    also_denied = _post(agency_client, "/api/v1/agency/customers", {"display_name": "Nope"})
    assert also_denied.status_code == 409


@pytest.mark.django_db
def test_capability_override_blocks_agency_create() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Caps", "life_caps", "oc@vokit.test")
    agency_id = agency.json()["data"]["id"]
    _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/capabilities",
        {"capabilities": {"create_customers": False}},
    )
    _user("agency-c@vokit.test", PrincipalType.AGENCY, "agency_owner", uuid.UUID(agency_id))
    agency_client = _client()
    _login(agency_client, "agency-c@vokit.test")
    denied = _post(agency_client, "/api/v1/agency/customers", {"display_name": "Blocked"})
    assert denied.status_code == 409


@pytest.mark.django_db
def test_banned_customer_create_is_generic() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Ban", "life_ban", "oban@vokit.test")
    agency_id = agency.json()["data"]["id"]
    added = _post(
        platform,
        "/api/v1/platform/risk/ban-keys",
        {"kind": "email", "value": "banned@vokit.test"},
    )
    assert added.status_code == 201
    denied = _post(
        platform,
        "/api/v1/platform/customers",
        {
            "display_name": "Banned",
            "agency_id": agency_id,
            "owner_email": "banned@vokit.test",
        },
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "customer_ineligible"


@pytest.mark.django_db
def test_reassignment_endpoint_is_forbidden() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Move", "life_move", "om@vokit.test")
    agency_id = agency.json()["data"]["id"]
    response = _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/reassign-customer",
        {"customer_id": str(new_uuid7())},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "customer_reassign_forbidden"


@pytest.mark.django_db
def test_finance_admin_cannot_create_agency() -> None:
    _user("finance@vokit.test", PrincipalType.PLATFORM, "finance_admin")
    client = _client()
    _login(client, "finance@vokit.test")
    response = _create_agency(client, "Nope", "life_nope", "x@vokit.test")
    assert response.status_code == 403


@pytest.mark.django_db
def test_customer_account_ignores_forged_customer_id() -> None:
    customer_id = new_uuid7()
    other_id = new_uuid7()
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Cust Agency",
            "legal_name": "Cust Agency",
            "owner_email": "ocust@vokit.test",
        },
    )
    agency_id = agency.json()["data"]["id"]
    created = _post(
        platform,
        "/api/v1/platform/customers",
        {
            "display_name": "Mine",
            "agency_id": agency_id,
            "customer_id": str(customer_id),
        },
    )
    assert created.status_code == 201
    _user(
        "cust@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        uuid.UUID(agency_id),
        customer_id,
    )
    client = _client()
    _login(client, "cust@vokit.test")
    ok = client.get("/api/v1/customer/account")
    assert ok.status_code == 200
    assert ok.json()["data"]["id"] == str(customer_id)
    forged = client.get(f"/api/v1/customer/account?customer_id={other_id}")
    assert forged.status_code == 404
