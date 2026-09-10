from __future__ import annotations

from pathlib import Path

import pytest
from django.test import Client
from django.urls import get_resolver

REQUIRED_TESTS = {
    "tenant": (
        "test_same_object_id_resolves_only_in_current_tenant",
        "test_missing_mapping_fails_closed",
        "test_disabled_tenant_cannot_be_routed",
        "test_outage_does_not_fall_back",
        "test_worker_job_cannot_cross_tenant",
        "test_pool_cannot_leak_tenant_context",
        "test_agency_forged_tenant_id_cannot_switch_db",
        "test_two_agencies_cannot_see_each_others_customers",
    ),
    "finance": (
        "test_duplicate_stripe_webhook_settles_once",
        "test_duplicate_payment_creates_one_commission",
        "test_appendix_c_example_1_normal_subscription",
        "test_appendix_c_example_2_independent_holds",
        "test_appendix_c_example_3_refund_during_hold",
        "test_appendix_c_example_4_chargeback_after_payout",
        "test_appendix_c_example_5_rate_change_snapshot",
        "test_concurrent_payouts_cannot_over_reserve",
        "test_agency_cannot_fetch_payout_proof",
        "test_mark_paid_is_blocked_without_proof",
        "test_chargeback_disables_agents_and_reverses_commission",
        "test_dashboards_are_portal_scoped_and_use_ledger_revenue",
    ),
    "voice": (
        "test_unpublished_agent_is_not_routable",
        "test_unpublished_agent_is_not_admitted",
        "test_continue_stops_after_grace",
        "test_continue_overage_keeps_call",
        "test_inbound_and_outbound_calls_are_recorded_in_metadata",
        "test_transfer_e164_queue_and_sip_client",
        "test_after_hours_inbound_and_outbound_voicemail_metadata",
        "test_internal_telephony_requires_service_token",
        "test_secrets_cannot_enter_prompts",
        "test_customer_a_cannot_use_customer_b_connection",
    ),
    "recording": (
        "test_recording_negative_matrix",
        "test_recording_outage_does_not_corrupt_call_and_orphans_are_visible",
        "test_internal_recording_requires_service_token",
        "test_object_key_is_tenant_partitioned",
    ),
}


def test_phase17_required_matrix_names_exist() -> None:
    root = Path(__file__).resolve().parent
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("test_*.py"))
    missing = [
        name
        for names in REQUIRED_TESTS.values()
        for name in names
        if f"def {name}(" not in text
    ]
    assert missing == []


def _named_paths() -> set[str]:
    names: set[str] = set()

    def walk(patterns) -> None:
        for pattern in patterns:
            if getattr(pattern, "name", None):
                names.add(pattern.name)
            walk(getattr(pattern, "url_patterns", ()))

    walk(get_resolver().url_patterns)
    return names


@pytest.mark.django_db
def test_impersonation_is_not_implemented() -> None:
    names = _named_paths()
    assert not any("impersonat" in name for name in names)
    client = Client()
    for path in (
        "/api/v1/platform/impersonate",
        "/api/v1/agency/impersonate",
        "/api/v1/customer/impersonate",
    ):
        response = client.get(path)
        assert response.status_code == 404
