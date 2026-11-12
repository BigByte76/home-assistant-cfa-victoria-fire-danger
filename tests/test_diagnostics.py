"""Tests for diagnostics."""

from __future__ import annotations

import json

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cfa_victoria_fire_danger.diagnostics import (
    async_get_config_entry_diagnostics,
)
from homeassistant.core import HomeAssistant


@pytest.mark.usefixtures("central_feed")
async def test_diagnostics(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Diagnostics are plain JSON with ISO dates."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, config_entry)

    # Must round-trip through the standard encoder without custom handling.
    assert json.loads(json.dumps(result)) == result
    assert result["entry_data"] == {"district": "central"}
    assert result["last_update_success"] is True
    assert result["forecast"][0] == {
        "date": "2026-11-12",
        "rating": "moderate",
        "total_fire_ban": False,
        "total_fire_ban_statement": (
            "Today, Thu, 12 Nov 2026 is not currently a day of Total Fire Ban."
        ),
        "issued_at": "2026-11-12T05:30:00+11:00",
    }
