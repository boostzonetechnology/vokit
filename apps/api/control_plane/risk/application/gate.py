from __future__ import annotations

import uuid

from control_plane.risk.application.ports import RiskCaseRepository
from control_plane.risk.domain.policies import assert_commercially_open


class CustomerRiskGate:
    def __init__(self, cases: RiskCaseRepository) -> None:
        self._cases = cases

    def assert_open(self, customer_id: uuid.UUID) -> None:
        case = self._cases.get_for_customer(customer_id)
        if case is None:
            assert_commercially_open(None)
            return
        assert_commercially_open(case.status, permanently_banned=case.permanently_banned)
