"""Diagnostics support for CFA Victoria Fire Danger."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import CFAConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CFAConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": dict(entry.data),
        "last_update_success": coordinator.last_update_success,
        "forecast": [
            {
                **asdict(day),
                # The diagnostics JSON encoder has no fallback for date objects.
                "date": day.date.isoformat(),
                "issued_at": day.issued_at.isoformat() if day.issued_at else None,
            }
            for day in (coordinator.data or {}).values()
        ],
    }
