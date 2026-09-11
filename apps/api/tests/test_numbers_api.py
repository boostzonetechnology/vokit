from __future__ import annotations

import json
import uuid
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.telephony.domain.types import ReservationStatus
from control_plane.telephony.models import PhoneNumberReservation
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"


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


def _ready_agency(platform: Client, suffix: str):
    agency = _create_agency(
        platform, f"Num {suffix}", f"num_{suffix}", f"oa-num-{suffix}@vokit.test"
    )
    assert agency.status_code == 200
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": f"Cust {suffix}", "agency_id": str(agency_id)},
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": f"Voice {suffix}",
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
    assert assigned.status_code == 201
    _user(
        f"agency-num-{suffix}@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    agency_client = _client()
    _login(agency_client, f"agency-num-{suffix}@vokit.test")
    created = _post(
        agency_client,
        "/api/v1/agency/agents",
        {"customer_id": str(customer_id), "display_name": f"Bot {suffix}"},
    )
    assert created.status_code == 201
    return {
        "agency_id": agency_id,
        "customer_id": customer_id,
        "agency_client": agency_client,
        "agent_id": created.json()["data"]["id"],
    }


def _stock(platform: Client, e164: str = "+14155550100", cost: int = 500) -> str:
    stocked = _post(
        platform,
        "/api/v1/platform/phone-numbers",
        {
            "e164": e164,
            "country": "US",
            "area": "415",
            "monthly_cost_minor": cost,
            "capabilities": ["voice"],
        },
    )
    assert stocked.status_code == 201
    return stocked.json()["data"]["id"]


@pytest.mark.django_db
def test_second_agency_cannot_take_reserved_number() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    first = _ready_agency(platform, "a")
    second = _ready_agency(platform, "b")
    number_id = _stock(platform)
    reserved = _post(
        first["agency_client"],
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": number_id, "agent_id": first["agent_id"]},
    )
    assert reserved.status_code == 201
    stolen = _post(
        second["agency_client"],
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": number_id, "agent_id": second["agent_id"]},
    )
    assert stolen.status_code == 409
    assert stolen.json()["error"]["code"] == "number_reserved"
    assigned = _post(
        second["agency_client"],
        "/api/v1/agency/phone-numbers/assignments",
        {"reservation_id": reserved.json()["data"]["id"], "confirm": True},
        HTTP_IDEMPOTENCY_KEY="steal-1",
    )
    assert assigned.status_code == 404


@pytest.mark.django_db
def test_assign_bills_customer_and_release_needs_confirm() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    ctx = _ready_agency(platform, "bill")
    number_id = _stock(platform, "+14155550111", 750)
    reserved = _post(
        ctx["agency_client"],
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": number_id, "agent_id": ctx["agent_id"]},
    )
    assert reserved.status_code == 201
    missing = _post(
        ctx["agency_client"],
        "/api/v1/agency/phone-numbers/assignments",
        {"reservation_id": reserved.json()["data"]["id"], "confirm": False},
        HTTP_IDEMPOTENCY_KEY="assign-no",
    )
    assert missing.status_code == 422
    assigned = _post(
        ctx["agency_client"],
        "/api/v1/agency/phone-numbers/assignments",
        {"reservation_id": reserved.json()["data"]["id"], "confirm": True},
        HTTP_IDEMPOTENCY_KEY="assign-yes",
    )
    assert assigned.status_code == 201
    invoice = assigned.json()["data"]["invoice"]
    assert invoice["kind"] == "number"
    assert invoice["total_minor"] == 750
    unconfirmed = _post(
        ctx["agency_client"],
        f"/api/v1/agency/phone-numbers/{number_id}/release",
        {"confirm": False},
    )
    assert unconfirmed.status_code == 422
    released = _post(
        ctx["agency_client"],
        f"/api/v1/agency/phone-numbers/{number_id}/release",
        {"confirm": True},
    )
    assert released.status_code == 200
    assert released.json()["data"]["status"] == "available"


@pytest.mark.django_db
def test_expired_reservation_can_be_taken_by_second_agency() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    first = _ready_agency(platform, "exp1")
    second = _ready_agency(platform, "exp2")
    number_id = _stock(platform, "+14155550200")
    reserved = _post(
        first["agency_client"],
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": number_id, "agent_id": first["agent_id"]},
    )
    assert reserved.status_code == 201
    row = PhoneNumberReservation.objects.get(id=reserved.json()["data"]["id"])
    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.status = ReservationStatus.ACTIVE.value
    row.save(update_fields=["expires_at"])
    taken = _post(
        second["agency_client"],
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": number_id, "agent_id": second["agent_id"]},
    )
    assert taken.status_code == 201
    assert taken.json()["data"]["agency_id"] == str(second["agency_id"])


@pytest.mark.django_db
def test_customer_cannot_purchase_numbers() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    ctx = _ready_agency(platform, "cust")
    _user(
        "cust-num@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=ctx["agency_id"],
        customer_id=ctx["customer_id"],
    )
    customer = _client()
    _login(customer, "cust-num@vokit.test")
    number_id = _stock(platform, "+14155550300")
    denied = _post(
        customer,
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": number_id, "agent_id": ctx["agent_id"]},
    )
    assert denied.status_code == 403


@pytest.mark.django_db
def test_internal_telephony_requires_service_token() -> None:
    response = _client().post("/internal/telephony/v1/did/resolve/")
    assert response.status_code == 401
