"""The CFA Victoria Fire Danger integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_DISTRICT, DISTRICTS
from .coordinator import CFAConfigEntry, CFACoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: CFAConfigEntry) -> bool:
    """Set up CFA Victoria Fire Danger from a config entry."""
    coordinator = CFACoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CFAConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: CFAConfigEntry) -> bool:
    """Migrate old config entries."""
    if entry.version > 2:
        # Downgraded from a future version.
        return False

    if entry.version == 1:
        # Version 1 stored the district display name, e.g. "North Central".
        name = entry.data.get(CONF_DISTRICT)
        slug = next((s for s, n in DISTRICTS.items() if n == name), None)
        if slug is None:
            _LOGGER.error("Cannot migrate config entry with unknown district %s", name)
            return False
        hass.config_entries.async_update_entry(
            entry,
            data={CONF_DISTRICT: slug},
            title=DISTRICTS[slug],
            unique_id=slug,
            version=2,
        )
        _LOGGER.debug("Migrated config entry %s to version 2", entry.entry_id)

    return True
