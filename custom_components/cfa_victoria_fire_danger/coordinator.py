"""Data update coordinator for CFA Victoria Fire Danger."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import TIMEZONE, CFAClient, CFAError, DayForecast
from .const import CONF_DISTRICT, DISTRICTS, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type CFAConfigEntry = ConfigEntry[CFACoordinator]


def _next_day_start() -> datetime:
    """Return one second past the next midnight in Victoria."""
    tomorrow = dt_util.now(TIMEZONE).date() + timedelta(days=1)
    return datetime.combine(tomorrow, time(0, 0, 1), tzinfo=TIMEZONE)


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

    @callback
    def async_track_day_rollover(self) -> CALLBACK_TYPE:
        """Re-evaluate entities at midnight in Victoria.

        Entities pick "today" and "tomorrow" when they write state. Without
        this, they would keep showing the previous day until the next poll.
        """
        unsub: CALLBACK_TYPE | None = None

        @callback
        def _rollover(_now: datetime) -> None:
            nonlocal unsub
            self.async_update_listeners()
            unsub = async_track_point_in_time(self.hass, _rollover, _next_day_start())

        unsub = async_track_point_in_time(self.hass, _rollover, _next_day_start())

        @callback
        def _cancel() -> None:
            if unsub is not None:
                unsub()

        return _cancel
