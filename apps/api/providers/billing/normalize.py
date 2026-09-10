from __future__ import annotations

import json
import uuid

from control_plane.billing.application.ports import NormalizedPaymentEvent
from shared_kernel.errors import DomainError
from shared_kernel.money import Money


def parse_payment_event(processor: str, raw_body: bytes) -> NormalizedPaymentEvent:
    try:
        data = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise DomainError("validation_error", "Webhook body is invalid.") from exc
    if not isinstance(data, dict):
        raise DomainError("validation_error", "Webhook body is invalid.")
    stripe_object = ((data.get("data") or {}) if isinstance(data.get("data"), dict) else {}).get(
        "object"
    )
    transaction = data.get("transaction") if isinstance(data.get("transaction"), dict) else {}
    source = stripe_object if isinstance(stripe_object, dict) else {}
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    event_id = str(
        data.get("event_id") or data.get("id") or transaction.get("id") or ""
    ).strip()
    invoice_raw = (
        data.get("invoice_id")
        or metadata.get("invoice_id")
        or transaction.get("invoice_id")
        or ""
    )
    amount_raw = (
        data.get("amount_minor")
        or source.get("amount")
        or transaction.get("amount_minor")
        or transaction.get("amount")
    )
    currency = str(
        data.get("currency") or source.get("currency") or transaction.get("currency") or "USD"
    ).upper()
    status = str(
        data.get("status") or data.get("type") or transaction.get("status") or ""
    ).lower()
    try:
        invoice_id = uuid.UUID(str(invoice_raw))
        amount_minor = int(amount_raw)
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("validation_error", "Webhook payment payload is invalid.") from exc
    from control_plane.risk.domain.types import CHARGEBACK_STATUSES, RISK_FLAG_STATUSES

    captured = status in {
        "captured",
        "succeeded",
        "settled",
        "payment_intent.succeeded",
        "transaction_settled",
        "transaction.settled",
    }
    chargeback = status in CHARGEBACK_STATUSES
    risk_flagged = status in RISK_FLAG_STATUSES
    return NormalizedPaymentEvent(
        processor=processor,
        event_id=event_id,
        invoice_id=invoice_id,
        amount=Money(amount_minor, currency),
        captured=captured and not chargeback,
        chargeback=chargeback,
        risk_flagged=risk_flagged and not chargeback,
    )
