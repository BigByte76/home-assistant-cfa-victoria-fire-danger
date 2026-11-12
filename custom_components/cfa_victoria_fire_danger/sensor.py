"""Fire danger rating sensors for CFA Victoria Fire Danger."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import RATINGS
from .coordinator import CFAConfigEntry
from .entity import CFAEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

SENSORS: tuple[tuple[SensorEntityDescription, int], ...] = tuple(
    (
        SensorEntityDescription(
            key=f"fire_danger_rating_{day}",
            translation_key=f"fire_danger_rating_{day}",
            device_class=SensorDeviceClass.ENUM,
            options=RATINGS,
        ),
        offset,
    )
    for offset, day in enumerate(("today", "tomorrow"))
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CFAConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up fire danger rating sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        CFAFireDangerRatingSensor(coordinator, description, offset)
        for description, offset in SENSORS
    )


# Ratings already reported as unknown, so each is logged once per run.
_WARNED_RATINGS: set[str] = set()


class CFAFireDangerRatingSensor(CFAEntity, SensorEntity):
    """Fire danger rating for one day."""

    @property
    def _rating(self) -> str | None:
        if (forecast := self.forecast) is None or forecast.rating is None:
            return None
        if forecast.rating not in RATINGS:
            if forecast.rating not in _WARNED_RATINGS:
                _WARNED_RATINGS.add(forecast.rating)
                _LOGGER.warning(
                    "Unknown fire danger rating %r for %s; please report it at "
                    "https://github.com/BigByte76/home-assistant-cfa-victoria-fire-danger/issues",
                    forecast.rating,
                    self.coordinator.district_name,
                )
            return None
        return forecast.rating

    @property
    def native_value(self) -> str | None:
        """Return the fire danger rating."""
        return self._rating

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Add the rating's position on the scale, for numeric comparisons."""
        attributes = super().extra_state_attributes
        if attributes is None:
            return None
        rating = self._rating
        return {**attributes, "level": RATINGS.index(rating) if rating else None}
