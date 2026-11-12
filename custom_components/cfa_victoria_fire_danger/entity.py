"""Base entity for CFA Victoria Fire Danger."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import TIMEZONE, DayForecast
from .const import ATTRIBUTION, DISTRICT_PAGE_URL, DOMAIN
from .coordinator import CFACoordinator


class CFAEntity(CoordinatorEntity[CFACoordinator]):
    """An entity reporting one forecast day for a CFA fire district."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CFACoordinator,
        description: EntityDescription,
        day_offset: int,
    ) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._day_offset = day_offset
        self._attr_unique_id = f"{coordinator.district}_{description.key}"
        page_slug = coordinator.district_name.lower().replace(" ", "-")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.district)},
            name=f"CFA {coordinator.district_name}",
            manufacturer="Country Fire Authority",
            model="Fire district",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=DISTRICT_PAGE_URL.format(page_slug=page_slug),
        )

    @property
    def forecast(self) -> DayForecast | None:
        """Return the forecast for this entity's day, in Melbourne local time."""
        day = dt_util.now(TIMEZONE).date() + timedelta(days=self._day_offset)
        return self.coordinator.data.get(day)

    @property
    def available(self) -> bool:
        """Return whether the feed currently covers this entity's day."""
        return super().available and self.forecast is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the forecast date and issue time."""
        if (forecast := self.forecast) is None:
            return None
        return {
            "date": forecast.date.isoformat(),
            "issued_at": forecast.issued_at.isoformat() if forecast.issued_at else None,
        }
