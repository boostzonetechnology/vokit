from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, replace

from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.telephony.domain.destinations import (
    DestinationKind,
    DestinationStatus,
    assert_destination_kind,
    edge_target,
)
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.media.domain import TransferDestinationRecord, TransferMemberRecord
from tenant.media.service import TenantMediaService

logger = logging.getLogger("vokit.telephony")


@dataclass(frozen=True, slots=True)
class CreateDestinationCommand:
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    kind: str
    label: str
    target: str = ""
    members: tuple[dict[str, str], ...] = ()
    no_answer_seconds: int = 25


class ManageDestinations:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        media: TenantMediaService,
        index,
        clock: Clock,
    ) -> None:
        self._customers = customers
        self._media = media
        self._index = index
        self._clock = clock

    def create(self, command: CreateDestinationCommand) -> TransferDestinationRecord:
        customer = self._customers.get(command.customer_id)
        if customer is None or customer.tenant_id != command.tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        kind = assert_destination_kind(command.kind)
        label = (command.label or "").strip()
        if not label:
            raise DomainError("validation_error", "label is required.")
        members = _members(kind, command.members)
        target = ""
        if kind is not DestinationKind.QUEUE:
            target = edge_target(kind, command.target)
        elif not members:
            raise DomainError("validation_error", "queue destinations need members.")
        now = self._clock.now()
        row = TransferDestinationRecord(
            destination_id=new_uuid7(),
            tenant_id=command.tenant_id,
            customer_id=command.customer_id,
            kind=kind,
            label=label[:128],
            target=target,
            members=members,
            no_answer_seconds=_timeout(command.no_answer_seconds),
            status=DestinationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        stored = self._media.put_destination(command.tenant_id, row)
        self._index.save(
            destination_id=stored.destination_id,
            tenant_id=stored.tenant_id,
            customer_id=stored.customer_id,
            kind=stored.kind.value,
            label=stored.label,
            status=stored.status.value,
            platform_disabled=False,
        )
        log_event(
            logger,
            "voice.destination.created",
            outcome="success",
            tenant_id=str(stored.tenant_id),
            destination_id=str(stored.destination_id),
            kind=stored.kind.value,
        )
        return stored

    def list(
        self, *, tenant_id: uuid.UUID, customer_id: uuid.UUID | None = None
    ) -> list[TransferDestinationRecord]:
        return self._media.list_destinations(tenant_id, customer_id=customer_id)

    def disable(
        self,
        *,
        destination_id: uuid.UUID,
        tenant_id: uuid.UUID | None,
        privileged: bool,
    ) -> TransferDestinationRecord:
        indexed = self._index.get(destination_id)
        if indexed is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if not privileged:
            if tenant_id is None or indexed.tenant_id != tenant_id:
                raise DomainError("not_found", "Resource not found.", http_status=404)
        row = self._media.get_destination(indexed.tenant_id, destination_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        stored = self._media.put_destination(
            indexed.tenant_id,
            replace(row, status=DestinationStatus.DISABLED, updated_at=self._clock.now()),
        )
        self._index.save(
            destination_id=stored.destination_id,
            tenant_id=stored.tenant_id,
            customer_id=stored.customer_id,
            kind=stored.kind.value,
            label=stored.label,
            status=stored.status.value,
            platform_disabled=privileged,
        )
        log_event(
            logger,
            "voice.destination.disabled",
            outcome="success",
            tenant_id=str(stored.tenant_id),
            destination_id=str(stored.destination_id),
            privileged=privileged,
        )
        return stored


def _timeout(raw: int) -> int:
    if type(raw) is not int or raw < 5 or raw > 120:
        raise DomainError("validation_error", "no_answer_seconds must be 5-120.")
    return raw


def _members(
    kind: DestinationKind, raw: tuple[dict[str, str], ...]
) -> tuple[TransferMemberRecord, ...]:
    if kind is not DestinationKind.QUEUE:
        return ()
    members: list[TransferMemberRecord] = []
    for item in raw:
        member_kind = assert_destination_kind(str(item.get("kind") or ""))
        if member_kind is DestinationKind.QUEUE:
            raise DomainError("validation_error", "queue members cannot be queues.")
        target = edge_target(member_kind, str(item.get("target") or ""))
        members.append(
            TransferMemberRecord(
                kind=member_kind,
                target=target,
                label=str(item.get("label") or "")[:128],
            )
        )
    return tuple(members)
