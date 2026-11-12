"""Total Fire Ban binary sensors for CFA Victoria Fire Danger."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CFAConfigEntry
from .entity import CFAEntity

PARALLEL_UPDATES = 0

BINARY_SENSORS: tuple[tuple[BinarySensorEntityDescription, int], ...] = tuple(
    (
        BinarySensorEntityDescription(
            key=f"total_fire_ban_{day}",
            translation_key=f"total_fire_ban_{day}",
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
    """Set up Total Fire Ban binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        CFATotalFireBanBinarySensor(coordinator, description, offset)
        for description, offset in BINARY_SENSORS
    )


class CFATotalFireBanBinarySensor(CFAEntity, BinarySensorEntity):
    """Whether a Total Fire Ban is declared for one day."""

    @property
    def is_on(self) -> bool | None:
        """Return true if a Total Fire Ban is in force."""
        if (forecast := self.forecast) is None:
            return None
        return forecast.total_fire_ban

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Add CFA's Total Fire Ban statement to the common attributes."""
        attributes = super().extra_state_attributes
        if attributes is None or (forecast := self.forecast) is None:
            return attributes
        return {**attributes, "statement": forecast.total_fire_ban_statement}
