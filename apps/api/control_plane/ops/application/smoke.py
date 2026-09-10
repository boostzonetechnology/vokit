from __future__ import annotations

import logging

from django.test import Client

from control_plane.ops.application.live_flags import (
    billing_is_live,
    calling_is_live,
    recordings_are_live,
)
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.ops")


class PostDeploySmoke:
    def execute(self) -> dict[str, object]:
        client = Client()
        health = client.get("/health")
        ready = client.get("/ready")
        api_health = client.get("/api/v1/health")
        checks = {
            "health": health.status_code,
            "ready": ready.status_code,
            "api_health": api_health.status_code,
            "calling_live": calling_is_live(),
            "billing_live": billing_is_live(),
            "recordings_live": recordings_are_live(),
        }
        failed = [
            name
            for name, status in (
                ("health", health.status_code),
                ("ready", ready.status_code),
                ("api_health", api_health.status_code),
            )
            if status != 200
        ]
        if failed:
            log_event(
                logger,
                "production.smoke.failed",
                outcome="denied",
                failed=",".join(failed),
            )
            raise DomainError(
                "post_deploy_smoke_failed",
                "Post-deploy smoke failed.",
                details={"checks": checks, "failed": failed},
                http_status=503,
            )
        log_event(logger, "production.smoke.passed", outcome="success")
        return {"status": "ok", "checks": checks}
