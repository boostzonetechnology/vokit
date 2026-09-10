"""Minute drain order: included → top-up → overage (Q-003). Money lives on invoices."""

from __future__ import annotations

from dataclasses import dataclass

from control_plane.billing.domain.types import DRAIN_ORDER, LotKind
from shared_kernel.errors import DomainError


@dataclass(frozen=True, slots=True)
class LotBalance:
    lot_id: str
    kind: LotKind
    remaining_minutes: int


@dataclass(frozen=True, slots=True)
class LotDrain:
    lot_id: str
    kind: LotKind
    minutes: int


def remaining_minutes(lots: tuple[LotBalance, ...]) -> int:
    return sum(max(0, lot.remaining_minutes) for lot in lots)


def drain_lots(lots: tuple[LotBalance, ...], minutes: int) -> tuple[LotDrain, ...]:
    if type(minutes) is not int or minutes < 0:
        raise DomainError("validation_error", "minutes must be a non-negative integer.")
    leftover = minutes
    drains: list[LotDrain] = []
    by_kind = {kind: [lot for lot in lots if lot.kind is kind] for kind in DRAIN_ORDER}
    for kind in DRAIN_ORDER:
        for lot in by_kind[kind]:
            if leftover <= 0:
                break
            take = min(max(0, lot.remaining_minutes), leftover)
            if take:
                drains.append(LotDrain(lot_id=lot.lot_id, kind=kind, minutes=take))
                leftover -= take
        if leftover <= 0:
            break
    if leftover > 0:
        raise DomainError(
            "minutes_exhausted",
            "Available minute lots cannot cover the requested usage.",
        )
    return tuple(drains)
