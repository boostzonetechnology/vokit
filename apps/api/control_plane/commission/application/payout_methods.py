from __future__ import annotations

import uuid
from dataclasses import dataclass

from control_plane.commission.application.ports import (
    PayoutMethodRecord,
    PayoutMethodRepository,
)
from control_plane.commission.domain.payout_method import build_method_label
from control_plane.commission.domain.types import PayoutMethodStatus
from control_plane.kyc.application.ports import KycCaseRepository
from control_plane.kyc.domain.types import KycStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.money import V1_CURRENCY


def _clean(value: object, *, field: str, max_len: int) -> str:
    text = str(value or "").strip()
    if not text:
        raise DomainError("validation_error", f"{field} is required.")
    return text[:max_len]


@dataclass(frozen=True, slots=True)
class UpsertPayoutMethodCommand:
    tenant_id: uuid.UUID
    beneficiary_name: str
    account_identifier: str
    bank_name: str
    country: str
    currency: str = V1_CURRENCY
    is_default: bool = False
    method_id: uuid.UUID | None = None


class ManageAgencyPayoutMethods:
    def __init__(
        self,
        methods: PayoutMethodRepository,
        cases: KycCaseRepository,
        clock: Clock,
    ) -> None:
        self._methods = methods
        self._cases = cases
        self._clock = clock

    def list(self, tenant_id: uuid.UUID) -> list[PayoutMethodRecord]:
        return self._methods.list_for_tenant(tenant_id)

    def get_for_tenant(
        self, tenant_id: uuid.UUID, method_id: uuid.UUID
    ) -> PayoutMethodRecord:
        row = self._methods.get(method_id)
        if row is None or row.tenant_id != tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return row

    def upsert(self, command: UpsertPayoutMethodCommand) -> PayoutMethodRecord:
        beneficiary = _clean(command.beneficiary_name, field="beneficiary_name", max_len=128)
        account = _clean(command.account_identifier, field="account_identifier", max_len=128)
        bank = _clean(command.bank_name, field="bank_name", max_len=128)
        country = _clean(command.country, field="country", max_len=2).upper()
        if len(country) != 2 or not country.isalpha():
            raise DomainError("validation_error", "country must be a 2-letter code.")
        currency = (command.currency or V1_CURRENCY).strip().upper()[:3] or V1_CURRENCY
        label = build_method_label(bank_name=bank, account_identifier=account)
        status = self._initial_status(command.tenant_id)
        now = self._clock.now()

        if command.method_id is not None:
            existing = self.get_for_tenant(command.tenant_id, command.method_id)
            if existing.status is PayoutMethodStatus.DISABLED:
                raise DomainError(
                    "validation_error",
                    "Disabled payout methods cannot be edited.",
                    http_status=409,
                )
            if command.is_default:
                self._methods.clear_default(command.tenant_id)
            updated = PayoutMethodRecord(
                id=existing.id,
                tenant_id=existing.tenant_id,
                beneficiary_name=beneficiary,
                account_identifier=account,
                bank_name=bank,
                country=country,
                currency=currency,
                label=label,
                status=existing.status,
                is_default=bool(command.is_default) or existing.is_default,
                created_at=existing.created_at,
                updated_at=now,
            )
            self._methods.update(updated)
            return updated

        if command.is_default:
            self._methods.clear_default(command.tenant_id)
        created = PayoutMethodRecord(
            id=new_uuid7(),
            tenant_id=command.tenant_id,
            beneficiary_name=beneficiary,
            account_identifier=account,
            bank_name=bank,
            country=country,
            currency=currency,
            label=label,
            status=status,
            is_default=bool(command.is_default),
            created_at=now,
            updated_at=now,
        )
        self._methods.create(created)
        return created

    def disable(self, tenant_id: uuid.UUID, method_id: uuid.UUID) -> PayoutMethodRecord:
        existing = self.get_for_tenant(tenant_id, method_id)
        if existing.status is PayoutMethodStatus.DISABLED:
            return existing
        updated = PayoutMethodRecord(
            id=existing.id,
            tenant_id=existing.tenant_id,
            beneficiary_name=existing.beneficiary_name,
            account_identifier=existing.account_identifier,
            bank_name=existing.bank_name,
            country=existing.country,
            currency=existing.currency,
            label=existing.label,
            status=PayoutMethodStatus.DISABLED,
            is_default=False,
            created_at=existing.created_at,
            updated_at=self._clock.now(),
        )
        self._methods.update(updated)
        return updated

    def enable(self, tenant_id: uuid.UUID, method_id: uuid.UUID) -> PayoutMethodRecord:
        existing = self.get_for_tenant(tenant_id, method_id)
        if existing.status is not PayoutMethodStatus.DISABLED:
            return existing
        status = self._initial_status(tenant_id)
        updated = PayoutMethodRecord(
            id=existing.id,
            tenant_id=existing.tenant_id,
            beneficiary_name=existing.beneficiary_name,
            account_identifier=existing.account_identifier,
            bank_name=existing.bank_name,
            country=existing.country,
            currency=existing.currency,
            label=existing.label,
            status=status,
            is_default=existing.is_default,
            created_at=existing.created_at,
            updated_at=self._clock.now(),
        )
        self._methods.update(updated)
        return updated

    def require_usable(
        self, tenant_id: uuid.UUID, method_id: uuid.UUID
    ) -> PayoutMethodRecord:
        row = self.get_for_tenant(tenant_id, method_id)
        if row.status is not PayoutMethodStatus.USABLE:
            raise DomainError(
                "payout_method_unusable",
                "Selected payout method is not available for withdrawal.",
                http_status=409,
            )
        return row

    def _initial_status(self, tenant_id: uuid.UUID) -> PayoutMethodStatus:
        case = self._cases.get_for_tenant(tenant_id)
        if case is not None and case.status is KycStatus.VERIFIED and not case.frozen:
            return PayoutMethodStatus.USABLE
        return PayoutMethodStatus.PENDING
