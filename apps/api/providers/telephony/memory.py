from __future__ import annotations

from control_plane.telephony.application.ports import ProviderNumberOffer
from shared_kernel.errors import DomainError
from shared_kernel.money import V1_CURRENCY, Money
from shared_kernel.phone import normalize_e164


class MemoryNumberProvider:
    """In-process catalog. Vendor SDKs stay out of the domain."""

    slug = "memory"

    def __init__(self) -> None:
        self._catalog: dict[str, ProviderNumberOffer] = {}
        self._owned: dict[str, ProviderNumberOffer] = {}
        self._purchases: dict[str, str] = {}

    def reset(self) -> None:
        self._catalog.clear()
        self._owned.clear()
        self._purchases.clear()

    def add_offer(
        self,
        e164: str,
        *,
        country: str = "US",
        area: str = "",
        capabilities: tuple[str, ...] = ("voice",),
        monthly_cost_minor: int = 200,
    ) -> ProviderNumberOffer:
        offer = ProviderNumberOffer(
            e164=normalize_e164(e164),
            country=country,
            area=area,
            capabilities=capabilities,
            monthly_cost=Money(monthly_cost_minor, V1_CURRENCY),
            provider=self.slug,
            provider_ref=f"mem_{normalize_e164(e164)}",
        )
        self._catalog[offer.e164] = offer
        return offer

    def search(
        self, *, country: str = "", area: str = "", capability: str = ""
    ) -> list[ProviderNumberOffer]:
        rows = []
        for offer in self._catalog.values():
            if offer.e164 in {item.e164 for item in self._owned.values()}:
                continue
            if country and offer.country.lower() != country.lower():
                continue
            if area and offer.area != area:
                continue
            if capability and capability.lower() not in offer.capabilities:
                continue
            rows.append(offer)
        return rows

    def purchase(self, *, e164: str, idempotency_key: str) -> ProviderNumberOffer:
        key = idempotency_key.strip()
        if key and key in self._purchases:
            ref = self._purchases[key]
            return self._owned[ref]
        normalized = normalize_e164(e164)
        existing = next(
            (row for row in self._owned.values() if row.e164 == normalized), None
        )
        if existing is not None:
            if key:
                self._purchases[key] = existing.provider_ref
            return existing
        offer = self._catalog.get(normalized)
        if offer is None:
            raise DomainError(
                "number_unavailable",
                "Number is not available from the provider.",
                http_status=409,
            )
        self._owned[offer.provider_ref] = offer
        if key:
            self._purchases[key] = offer.provider_ref
        return offer

    def release(self, *, provider_ref: str) -> None:
        self._owned.pop(provider_ref, None)

    def owned_refs(self) -> set[str]:
        return set(self._owned)
