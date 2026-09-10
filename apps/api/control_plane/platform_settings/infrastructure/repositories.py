from __future__ import annotations

from control_plane.platform_settings.application.ports import AgencyFlagRecord, SettingRecord
from control_plane.platform_settings.models import AgencyFeatureFlag, PlatformSetting


class DjangoSettingRepository:
    def get(self, key: str) -> SettingRecord | None:
        row = PlatformSetting.objects.filter(key=key).first()
        if row is None:
            return None
        return SettingRecord(
            key=row.key,
            value=row.value,
            secret=row.secret,
            updated_by_id=row.updated_by_id,
        )

    def upsert(self, record: SettingRecord) -> SettingRecord:
        PlatformSetting.objects.update_or_create(
            key=record.key,
            defaults={
                "value": record.value,
                "secret": record.secret,
                "updated_by_id": record.updated_by_id,
            },
        )
        stored = self.get(record.key)
        return stored or record

    def list_all(self) -> list[SettingRecord]:
        return [
            SettingRecord(
                key=row.key,
                value=row.value,
                secret=row.secret,
                updated_by_id=row.updated_by_id,
            )
            for row in PlatformSetting.objects.order_by("key")
        ]


class DjangoAgencyFlagRepository:
    def list_all(self) -> list[AgencyFlagRecord]:
        return [
            AgencyFlagRecord(
                tenant_id=row.tenant_id,
                flag=row.flag,
                enabled=row.enabled,
                updated_by_id=row.updated_by_id,
            )
            for row in AgencyFeatureFlag.objects.order_by("tenant_id", "flag")
        ]

    def upsert(self, record: AgencyFlagRecord) -> AgencyFlagRecord:
        AgencyFeatureFlag.objects.update_or_create(
            tenant_id=record.tenant_id,
            flag=record.flag,
            defaults={
                "enabled": record.enabled,
                "updated_by_id": record.updated_by_id,
            },
        )
        return record
