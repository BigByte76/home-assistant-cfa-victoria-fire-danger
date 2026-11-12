"""Tests for setup, entities and migration."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.cfa_victoria_fire_danger.const import CONF_DISTRICT, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .conftest import CENTRAL_URL, FIXTURE_NOW, load_fixture


@pytest.mark.freeze_time(FIXTURE_NOW)
@pytest.mark.usefixtures("central_feed")
async def test_setup_and_entities(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Entities report today's and tomorrow's forecast."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    today = hass.states.get("sensor.cfa_central_fire_danger_rating_today")
    assert today.state == "moderate"
    assert today.attributes["date"] == "2026-11-12"
    assert today.attributes["issued_at"] == "2026-11-12T05:30:00+11:00"
    assert (
        hass.states.get("sensor.cfa_central_fire_danger_rating_tomorrow").state
        == "no_rating"
    )
    ban_today = hass.states.get("binary_sensor.cfa_central_total_fire_ban_today")
    assert ban_today.state == "off"
    assert ban_today.attributes["statement"] == (
        "Today, Thu, 12 Nov 2026 is not currently a day of Total Fire Ban."
    )
    assert (
        hass.states.get("binary_sensor.cfa_central_total_fire_ban_tomorrow").state
        == "off"
    )

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retry_on_bad_feed(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    """An unreadable feed puts the entry into setup retry."""
    aioclient_mock.get(CENTRAL_URL, text="<html><p>error<br></p></html>")
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_migrate_v1_entry(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Version 1 entries stored the district display name."""
    aioclient_mock.get(
        CENTRAL_URL.replace("central", "northcentral"),
        content=load_fixture("central.xml"),
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CFA North Central",
        data={CONF_DISTRICT: "North Central"},
        version=1,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.version == 2
    assert entry.data == {CONF_DISTRICT: "northcentral"}
    assert entry.unique_id == "northcentral"
    assert entry.title == "North Central"
