from __future__ import annotations

import logging
import uuid

from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.platform_settings.application.ports import (
    AgencyFlagRecord,
    AgencyFlagRepository,
    SettingRecord,
    SettingRepository,
)
from control_plane.platform_settings.domain.policies import (
    assert_flag,
    assert_setting_key,
    coerce_value,
    public_value,
)
from control_plane.platform_settings.domain.types import SETTING_CATALOG
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.settings")


class PlatformSettingsControl:
    def __init__(self, settings: SettingRepository, flags: AgencyFlagRepository) -> None:
        self._settings = settings
        self._flags = flags

    def ensure_defaults(self) -> None:
        from django.conf import settings

        live_default = bool(getattr(settings, "LIVE_FLAGS_ENABLED_BY_DEFAULT", False))
        for spec in SETTING_CATALOG.values():
            if self._settings.get(spec.key) is None:
                value = spec.default
                if spec.key in {
                    "flags.calling_live",
                    "flags.billing_live",
                    "flags.recordings_live",
                }:
                    value = live_default
                self._settings.upsert(
                    SettingRecord(
                        key=spec.key,
                        value=value,
                        secret=spec.secret,
                        updated_by_id=None,
                    )
                )

    def snapshot(self) -> dict[str, object]:
        self.ensure_defaults()
        rows = {row.key: row for row in self._settings.list_all()}
        settings = []
        for spec in SETTING_CATALOG.values():
            row = rows.get(spec.key)
            stored = spec.default if row is None else row.value
            settings.append(
                {
                    "key": spec.key,
                    "value": public_value(spec, stored),
                    "secret": spec.secret,
                    "has_value": stored not in (None, ""),
                }
            )
        flags = [
            {
                "agency_id": str(row.tenant_id),
                "flag": row.flag,
                "enabled": row.enabled,
            }
            for row in self._flags.list_all()
        ]
        return {"settings": settings, "agency_flags": flags}

    def live_flag(self, name: str) -> bool:
        from django.conf import settings

        row = self._settings.get(f"flags.{name}")
        if row is None:
            return bool(getattr(settings, "LIVE_FLAGS_ENABLED_BY_DEFAULT", False))
        return row.value is True

    def mfa_required_privileged(self) -> bool:
        self.ensure_defaults()
        row = self._settings.get("security.mfa_required_privileged")
        if row is None:
            return False
        return row.value is True

    def hold_days(self) -> int:
        self.ensure_defaults()
        row = self._settings.get("payout.hold_days")
        if row is None:
            return 15
        try:
            value = int(row.value)
        except (TypeError, ValueError):
            return 15
        if value < 0 or value > 365:
            return 15
        return value

    def update(
        self,
        *,
        key: str,
        value: object,
        reason: str,
        actor_id: uuid.UUID,
        actor_role: str,
        ip: str = "",
        user_agent: str = "",
    ) -> dict[str, object]:
        spec = assert_setting_key(key)
        cleaned_reason = reason.strip()
        if not cleaned_reason:
            raise DomainError("validation_error", "reason is required.")
        coerced = coerce_value(spec, value)
        before = self._settings.get(spec.key)
        self._settings.upsert(
            SettingRecord(
                key=spec.key,
                value=coerced,
                secret=spec.secret,
                updated_by_id=actor_id,
            )
        )
        record_audit().execute(
            RecordAuditCommand(
                action="settings.changed",
                entity_type="platform_setting",
                entity_id=spec.key,
                actor_id=actor_id,
                actor_role=actor_role,
                reason=cleaned_reason,
                before_summary=str(before.value) if before and not spec.secret else "",
                after_summary="" if spec.secret else str(coerced),
                payload={"key": spec.key, "secret": spec.secret},
                ip=ip,
                user_agent=user_agent,
            )
        )
        log_event(logger, "settings.changed", outcome="success", key=spec.key)
        return self.snapshot()

    def set_agency_flag(
        self,
        *,
        tenant_id: uuid.UUID,
        flag: str,
        enabled: bool,
        reason: str,
        actor_id: uuid.UUID,
        actor_role: str,
        ip: str = "",
        user_agent: str = "",
    ) -> dict[str, object]:
        name = assert_flag(flag)
        cleaned_reason = reason.strip()
        if not cleaned_reason:
            raise DomainError("validation_error", "reason is required.")
        if type(enabled) is not bool:
            raise DomainError("validation_error", "enabled must be a boolean.")
        self._flags.upsert(
            AgencyFlagRecord(
                tenant_id=tenant_id,
                flag=name,
                enabled=enabled,
                updated_by_id=actor_id,
            )
        )
        record_audit().execute(
            RecordAuditCommand(
                action="settings.flag_changed",
                entity_type="agency_feature_flag",
                entity_id=name,
                actor_id=actor_id,
                actor_role=actor_role,
                tenant_id=tenant_id,
                reason=cleaned_reason,
                after_summary="enabled" if enabled else "disabled",
                payload={"flag": name, "enabled": enabled},
                ip=ip,
                user_agent=user_agent,
            )
        )
        log_event(
            logger,
            "settings.flag_changed",
            outcome="success",
            flag=name,
            tenant_id=str(tenant_id),
        )
        return self.snapshot()
