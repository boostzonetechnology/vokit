from __future__ import annotations

import uuid

import pytest

from control_plane.integrations.domain.policies import (
    assert_action,
    assert_events,
    assert_provider,
    assert_same_customer,
    assert_webhook_url,
    provider_supports_action,
)
from control_plane.integrations.domain.types import ProviderKind
from shared_kernel.errors import DomainError
from shared_kernel.hmac import sign_hmac_raw


def test_providers_and_actions_are_customer_scoped() -> None:
    assert assert_provider("HubSpot") is ProviderKind.HUBSPOT
    assert assert_action("create_lead") == "create_lead"
    with pytest.raises(DomainError):
        assert_action("transfer_call")
    with pytest.raises(DomainError):
        assert_action("drop_database")
    assert provider_supports_action(ProviderKind.HUBSPOT, "create_lead")
    assert not provider_supports_action(ProviderKind.QUICKBOOKS, "create_lead")


def test_webhook_url_rejects_ssrf_and_events_are_allowlisted() -> None:
    assert_webhook_url("https://hooks.example.test/vokit", allow_http=False)
    with pytest.raises(DomainError):
        assert_webhook_url("http://hooks.example.test/vokit", allow_http=False)
    with pytest.raises(DomainError):
        assert_webhook_url("https://127.0.0.1/hook", allow_http=True)
    with pytest.raises(DomainError):
        assert_webhook_url("https://localhost/hook", allow_http=True)
    assert assert_events(["call.completed"]) == ("call.completed",)
    with pytest.raises(DomainError):
        assert_events(["not.an.event"])


def test_foreign_customer_is_not_found_and_signatures_are_stable() -> None:
    customer = uuid.uuid4()
    assert_same_customer(connection_customer=customer, actor_customer=customer)
    with pytest.raises(DomainError) as exc:
        assert_same_customer(connection_customer=customer, actor_customer=uuid.uuid4())
    assert exc.value.http_status == 404
    body = b'{"event_type":"call.completed"}'
    assert sign_hmac_raw(secret="one", raw_body=body) != sign_hmac_raw(
        secret="two", raw_body=body
    )
