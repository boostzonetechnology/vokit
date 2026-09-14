from __future__ import annotations

import pytest

from control_plane.agents.infrastructure.container import reset_vectors
from control_plane.integrations.infrastructure.container import reset_integrations
from control_plane.recordings.infrastructure.container import reset_recording_store
from control_plane.telephony.infrastructure.container import reset_number_provider
from control_plane.tenancy.infrastructure.container import reset_runtime


@pytest.fixture(autouse=True)
def _reset_tenant_runtime() -> None:
    reset_runtime()
    reset_vectors()
    reset_number_provider()
    reset_recording_store()
    reset_integrations()
    yield
    reset_runtime()
    reset_vectors()
    reset_number_provider()
    reset_recording_store()
    reset_integrations()


@pytest.fixture(autouse=True)
def _seed_rbac(db) -> None:
    """Idempotently seed RBAC permission catalog and system roles before every DB test.

    ADR-007: permissions_for_role() and assert_role_matches_principal() now query
    the database; this fixture ensures the tables are populated so domain tests,
    API tests, and command tests all find the expected roles and permissions.
    """
    from control_plane.identity.infrastructure.rbac_seed import ensure_rbac_seeded

    ensure_rbac_seeded()
