"""Tests for setup, entities and migration."""

from __future__ import annotations

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.cfa_victoria_fire_danger import sensor as sensor_module
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
    assert today.attributes["level"] == 1
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


@pytest.mark.freeze_time("2026-11-12 23:59:30+11:00")
async def test_day_rollover_at_midnight(
    hass: HomeAssistant,
    central_feed: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Entities move to the next day at midnight without waiting for a poll."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    today_id = "sensor.cfa_central_fire_danger_rating_today"
    assert hass.states.get(today_id).attributes["date"] == "2026-11-12"
    assert hass.states.get(today_id).state == "moderate"

    freezer.move_to("2026-11-13 00:00:02+11:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    today = hass.states.get(today_id)
    assert today.attributes["date"] == "2026-11-13"
    assert today.state == "no_rating"
    assert (
        hass.states.get("sensor.cfa_central_fire_danger_rating_tomorrow").attributes[
            "date"
        ]
        == "2026-11-14"
    )
    # Served from cached data: the feed was only fetched once.
    assert central_feed.call_count == 1


@pytest.mark.freeze_time(FIXTURE_NOW)
async def test_unknown_rating_logged_once(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unrecognised rating is unknown and warned about only once."""
    sensor_module._WARNED_RATINGS.clear()
    aioclient_mock.get(
        CENTRAL_URL,
        content=b"""<rss><channel><item><title>Thursday, 12 November 2026</title>
        <description>&lt;p&gt;Central: SEVERE&lt;/p&gt;</description>
        </item></channel></rss>""",
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    today = hass.states.get("sensor.cfa_central_fire_danger_rating_today")
    assert today.state == "unknown"
    assert today.attributes["level"] is None

    await config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert caplog.text.count("Unknown fire danger rating 'severe'") == 1
