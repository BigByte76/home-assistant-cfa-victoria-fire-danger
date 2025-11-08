"""CFA Victoria Fire Danger custom integration."""
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import Entity
import aiohttp
import xml.etree.ElementTree as ET
import logging

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)

async def async_setup_entry(hass, entry):
    district = entry.data["district"]
    coordinator = CFAVictoriaCoordinator(hass, district)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault("cfa_victoria_fire_danger", {})[entry.entry_id] = coordinator
    hass.config_entries.async_setup_platforms(entry, ["sensor"])
    return True

async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data["cfa_victoria_fire_danger"].pop(entry.entry_id)
    return unload_ok

class CFAVictoriaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, district):
        super().__init__(hass, _LOGGER, name="CFA Victoria Fire Danger", update_interval=SCAN_INTERVAL)
        self.district = district

    async def _async_update_data(self):
        url = f"https://www.cfa.vic.gov.au/feeds/firedangerrating_{self.district}.xml"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    text = await resp.text()
                    root = ET.fromstring(text)
                    items = root.findall(".//item")
                    today, tomorrow = None, None
                    if items:
                        today = items[0].findtext("title")
                        if len(items) > 1:
                            tomorrow = items[1].findtext("title")
                    return {"today": today, "tomorrow": tomorrow}
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
