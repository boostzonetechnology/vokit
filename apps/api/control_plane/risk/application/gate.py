from __future__ import annotations

import uuid

from control_plane.risk.application.ports import RiskCaseRepository
from control_plane.risk.domain.policies import (
    assert_commercially_open,
    assert_new_commercial_open,
)
from control_plane.risk.domain.types import RiskStatus


class CustomerRiskGate:
    def __init__(self, cases: RiskCaseRepository) -> None:
        self._cases = cases

    def _status(self, customer_id: uuid.UUID) -> tuple[RiskStatus | None, bool]:
        case = self._cases.get_for_customer(customer_id)
        if case is None:
            return None, False
        return case.status, case.permanently_banned

    def assert_open(self, customer_id: uuid.UUID) -> None:
        status, banned = self._status(customer_id)
        assert_commercially_open(status, permanently_banned=banned)

    def assert_new_commercial(self, customer_id: uuid.UUID) -> None:
        status, banned = self._status(customer_id)
        assert_new_commercial_open(status, permanently_banned=banned)
