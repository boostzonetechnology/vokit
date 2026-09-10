from __future__ import annotations

import json
import logging

from shared_kernel.logging import StructuredJsonFormatter, log_event


def test_redacts_secret_fields(caplog: logging.LogCaptureFixture) -> None:
    logger = logging.getLogger("vokit.test")
    with caplog.at_level(logging.INFO, logger="vokit.test"):
        log_event(logger, "demo", password="hunter2", token="abc", path="/health")
    assert "hunter2" not in caplog.text
    assert "abc" not in caplog.text


def test_json_formatter_includes_correlation() -> None:
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord("vokit.test", logging.INFO, __file__, 1, "hello", (), None)
    record.correlation_id = "cid-1"
    record.event = "unit"
    record.vokit = {"password": "nope", "outcome": "success"}
    payload = json.loads(formatter.format(record))
    assert payload["event"] == "unit"
    assert payload["correlation_id"] == "cid-1"
    assert payload["password"] == "[redacted]"
    assert payload["outcome"] == "success"
