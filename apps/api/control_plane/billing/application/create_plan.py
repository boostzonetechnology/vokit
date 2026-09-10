from __future__ import annotations

import logging
from dataclasses import dataclass

from control_plane.billing.application.ports import (
    PlanRecord,
    PlanRepository,
    PlanVersionRecord,
    PlanVersionRepository,
)
from control_plane.billing.domain.policies import assert_grace_seconds, assert_positive_minutes
from control_plane.billing.domain.types import PlanStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from shared_kernel.money import Money

logger = logging.getLogger("vokit.billing")


@dataclass(frozen=True, slots=True)
class CreatePlanCommand:
    name: str
    price_minor: int
    included_minutes: int
    allow_topups: bool
    topup_minutes: int
    topup_price_minor: int
    overage_enabled: bool
    overage_price_per_minute_minor: int
    grace_seconds: int


class CreatePlan:
    def __init__(
        self,
        plans: PlanRepository,
        versions: PlanVersionRepository,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._versions = versions
        self._clock = clock

    def execute(self, command: CreatePlanCommand) -> tuple[PlanRecord, PlanVersionRecord]:
        name = command.name.strip()
        if not name:
            raise DomainError("validation_error", "name is required.")
        price = Money(command.price_minor)
        topup_price = Money(command.topup_price_minor)
        overage = Money(command.overage_price_per_minute_minor)
        assert_positive_minutes(command.included_minutes, field="included_minutes")
        assert_positive_minutes(command.topup_minutes, field="topup_minutes")
        assert_grace_seconds(command.grace_seconds)
        if command.allow_topups and command.topup_minutes < 1:
            raise DomainError("validation_error", "topup_minutes must be positive.")
        now = self._clock.now()
        plan = PlanRecord(id=new_uuid7(), name=name, status=PlanStatus.ACTIVE, created_at=now)
        version = PlanVersionRecord(
            id=new_uuid7(),
            plan_id=plan.id,
            version=1,
            price=price,
            included_minutes=command.included_minutes,
            allow_topups=command.allow_topups,
            topup_minutes=command.topup_minutes,
            topup_price=topup_price,
            overage_enabled=command.overage_enabled,
            overage_price_per_minute=overage,
            grace_seconds=command.grace_seconds,
            used_at=None,
            created_at=now,
        )
        self._plans.create(plan)
        self._versions.create(version)
        log_event(logger, "billing.plan.created", outcome="success", plan_id=str(plan.id))
        return plan, version
