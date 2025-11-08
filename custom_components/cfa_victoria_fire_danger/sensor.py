from homeassistant.components.sensor import SensorEntity
from . import CFAVictoriaCoordinator
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CFAVictoriaSensor(coordinator, "today"), CFAVictoriaSensor(coordinator, "tomorrow")])

class CFAVictoriaSensor(SensorEntity):
    def __init__(self, coordinator, day):
        self.coordinator = coordinator
        self.day = day
        self._attr_name = f"CFA Fire Danger {day.title()} ({coordinator.district})"
        self._attr_unique_id = f"{coordinator.district}_{day}_fire_danger"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.day)

    async def async_update(self):
        await self.coordinator.async_request_refresh()
