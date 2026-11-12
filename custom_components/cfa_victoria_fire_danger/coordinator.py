"""Data update coordinator for CFA Victoria Fire Danger."""

from __future__ import annotations

from datetime import date
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CFAClient, CFAError, DayForecast
from .const import CONF_DISTRICT, DISTRICTS, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type CFAConfigEntry = ConfigEntry[CFACoordinator]


class CFACoordinator(DataUpdateCoordinator[dict[date, DayForecast]]):
    """Polls the CFA feed for one fire district."""

    config_entry: CFAConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: CFAConfigEntry) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.district: str = config_entry.data[CONF_DISTRICT]
        self.district_name = DISTRICTS[self.district]
        self.client = CFAClient(async_get_clientsession(hass))

    async def _async_update_data(self) -> dict[date, DayForecast]:
        try:
            return await self.client.async_get_forecast(
                self.district, self.district_name
            )
        except CFAError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
