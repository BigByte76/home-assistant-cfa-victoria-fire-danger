"""Tests for the CFA Victoria Fire Danger config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.cfa_victoria_fire_danger.const import CONF_DISTRICT, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import CENTRAL_URL

SETUP_ENTRY = "custom_components.cfa_victoria_fire_danger.async_setup_entry"


@pytest.mark.usefixtures("central_feed")
async def test_user_flow(hass: HomeAssistant) -> None:
    """Choosing a district creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with patch(SETUP_ENTRY, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DISTRICT: "central"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Central"
    assert result["data"] == {CONF_DISTRICT: "central"}
    assert result["result"].unique_id == "central"


@pytest.mark.parametrize(
    ("mock_kwargs", "error"),
    [
        ({"exc": TimeoutError}, "cannot_connect"),
        ({"status": 404}, "cannot_connect"),
        ({"text": "<html><p>oops<br></p></html>"}, "invalid_response"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_kwargs: dict,
    error: str,
) -> None:
    """Feed problems are shown as form errors."""
    aioclient_mock.get(CENTRAL_URL, **mock_kwargs)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DISTRICT: "central"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


async def test_user_flow_already_configured(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A district can only be added once."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DISTRICT: "central"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
