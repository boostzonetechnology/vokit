from __future__ import annotations

from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.reporting.application.dashboard import DashboardQueries


def dashboards() -> DashboardQueries:
    return DashboardQueries(SystemClock())
