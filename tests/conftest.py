"""Shared fixtures for CFA Victoria Fire Danger tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.cfa_victoria_fire_danger.const import CONF_DISTRICT, DOMAIN
from homeassistant.core import HomeAssistant

CENTRAL_URL = "https://www.cfa.vic.gov.au/cfa/rssfeed/central-firedistrict_rss.xml"
# The fixture feed was captured on this date (Melbourne time).
FIXTURE_NOW = "2026-11-12 10:00:00+11:00"


def load_fixture(name: str) -> bytes:
    """Load a fixture file."""
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in all tests."""


@pytest.fixture
def central_feed(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Serve the captured Central district feed."""
    aioclient_mock.get(CENTRAL_URL, content=load_fixture("central.xml"))
    return aioclient_mock


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a config entry for the Central district."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Central",
        data={CONF_DISTRICT: "central"},
        unique_id="central",
        version=2,
    )
    entry.add_to_hass(hass)
    return entry
