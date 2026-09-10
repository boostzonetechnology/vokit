from __future__ import annotations

from dataclasses import dataclass

from control_plane.billing.application.ports import (
    PlanRecord,
    PlanRepository,
    PlanVersionRecord,
    PlanVersionRepository,
)
from control_plane.billing.domain.policies import (
    assert_grace_seconds,
    assert_plan_version_mutable,
    assert_positive_minutes,
)
from control_plane.billing.domain.types import PlanStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.money import Money


@dataclass(frozen=True, slots=True)
class AddPlanVersionCommand:
    plan_id: object
    price_minor: int
    included_minutes: int
    allow_topups: bool
    topup_minutes: int
    topup_price_minor: int
    overage_enabled: bool
    overage_price_per_minute_minor: int
    grace_seconds: int


@dataclass(frozen=True, slots=True)
class UpdatePlanVersionCommand:
    version_id: object
    price_minor: int
    included_minutes: int
    allow_topups: bool
    topup_minutes: int
    topup_price_minor: int
    overage_enabled: bool
    overage_price_per_minute_minor: int
    grace_seconds: int


def version_terms(command) -> dict:
    assert_positive_minutes(command.included_minutes, field="included_minutes")
    assert_positive_minutes(command.topup_minutes, field="topup_minutes")
    assert_grace_seconds(command.grace_seconds)
    if command.allow_topups and command.topup_minutes < 1:
        raise DomainError("validation_error", "topup_minutes must be positive.")
    return {
        "price": Money(command.price_minor),
        "included_minutes": command.included_minutes,
        "allow_topups": command.allow_topups,
        "topup_minutes": command.topup_minutes,
        "topup_price": Money(command.topup_price_minor),
        "overage_enabled": command.overage_enabled,
        "overage_price_per_minute": Money(command.overage_price_per_minute_minor),
        "grace_seconds": command.grace_seconds,
    }


class AddPlanVersion:
    def __init__(
        self, plans: PlanRepository, versions: PlanVersionRepository, clock: Clock
    ) -> None:
        self._plans = plans
        self._versions = versions
        self._clock = clock

    def execute(self, command: AddPlanVersionCommand) -> PlanVersionRecord:
        plan = self._plans.get(command.plan_id)  # type: ignore[arg-type]
        if plan is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if plan.status is PlanStatus.ARCHIVED:
            raise DomainError(
                "plan_archived",
                "Archived plans cannot gain versions.",
                http_status=409,
            )
        version = PlanVersionRecord(
            id=new_uuid7(),
            plan_id=plan.id,
            version=self._versions.next_version(plan.id),
            used_at=None,
            created_at=self._clock.now(),
            **version_terms(command),
        )
        self._versions.create(version)
        return version


class UpdatePlanVersion:
    def __init__(self, versions: PlanVersionRepository) -> None:
        self._versions = versions

    def execute(self, command: UpdatePlanVersionCommand) -> PlanVersionRecord:
        current = self._versions.get(command.version_id)  # type: ignore[arg-type]
        if current is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        assert_plan_version_mutable(used=current.used_at is not None)
        updated = PlanVersionRecord(
            id=current.id,
            plan_id=current.plan_id,
            version=current.version,
            used_at=None,
            created_at=current.created_at,
            **version_terms(command),
        )
        self._versions.update(updated)
        return updated


class ArchivePlan:
    def __init__(self, plans: PlanRepository) -> None:
        self._plans = plans

    def execute(self, plan_id: object) -> PlanRecord:
        plan = self._plans.get(plan_id)  # type: ignore[arg-type]
        if plan is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        updated = PlanRecord(
            id=plan.id,
            name=plan.name,
            status=PlanStatus.ARCHIVED,
            created_at=plan.created_at,
        )
        self._plans.update(updated)
        return updated
