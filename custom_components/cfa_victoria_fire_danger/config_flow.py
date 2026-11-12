"""Config flow for CFA Victoria Fire Danger."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import CFAClient, CFAConnectionError, CFAParseError
from .const import CONF_DISTRICT, DISTRICTS, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DISTRICT): SelectSelector(
            SelectSelectorConfig(
                options=list(DISTRICTS),
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_DISTRICT,
            )
        )
    }
)


class CFAConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CFA Victoria Fire Danger."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick a fire district."""
        errors: dict[str, str] = {}
        if user_input is not None:
            district = user_input[CONF_DISTRICT]
            await self.async_set_unique_id(district)
            self._abort_if_unique_id_configured()

            client = CFAClient(async_get_clientsession(self.hass))
            try:
                await client.async_get_forecast(district, DISTRICTS[district])
            except CFAConnectionError:
                errors["base"] = "cannot_connect"
            except CFAParseError:
                errors["base"] = "invalid_response"
            except Exception:
                _LOGGER.exception("Unexpected error validating CFA feed")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=DISTRICTS[district], data={CONF_DISTRICT: district}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, user_input
            ),
            errors=errors,
        )
