from __future__ import annotations

import logging
import uuid

from config.celery import app
from shared_kernel.http.correlation import set_correlation_id
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.agents")


@app.task(name="agents.process_knowledge")
def process_knowledge_source_task(
    source_id: str,
    tenant_id: str | None = None,
    correlation_id: str = "",
) -> None:
    if correlation_id:
        set_correlation_id(correlation_id)
    from control_plane.agents.infrastructure.container import process_knowledge

    result = process_knowledge().execute(
        source_id=uuid.UUID(source_id),
        tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
    )
    if result.get("status") != "ready":
        log_event(
            logger,
            "knowledge.ingest.failed",
            outcome="failure",
            source_id=source_id,
            tenant_id=tenant_id,
            error=str(result.get("error") or result.get("status") or ""),
        )
