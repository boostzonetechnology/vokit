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
