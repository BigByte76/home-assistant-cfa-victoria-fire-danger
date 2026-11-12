"""Constants for the CFA Victoria Fire Danger integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "cfa_victoria_fire_danger"

CONF_DISTRICT: Final = "district"

# Feed slug -> district name exactly as it appears in the feed text.
DISTRICTS: Final[dict[str, str]] = {
    "central": "Central",
    "eastgippsland": "East Gippsland",
    "mallee": "Mallee",
    "northcentral": "North Central",
    "northeast": "North East",
    "northerncountry": "Northern Country",
    "southwest": "South West",
    "westandsouthgippsland": "West and South Gippsland",
    "wimmera": "Wimmera",
}

# Australian Fire Danger Rating System levels, normalised to snake_case.
RATINGS: Final[list[str]] = [
    "no_rating",
    "moderate",
    "high",
    "extreme",
    "catastrophic",
]

UPDATE_INTERVAL: Final = timedelta(minutes=15)

ATTRIBUTION: Final = "Data provided by the Country Fire Authority (CFA), Victoria"

DISTRICT_PAGE_URL: Final = (
    "https://www.cfa.vic.gov.au/warnings-and-restrictions/"
    "fire-bans-ratings-and-restrictions/total-fire-bans-fire-danger-ratings/"
    "{page_slug}-fire-district"
)

DISTRICT_MAP_URL: Final = "https://www.cfa.vic.gov.au/warnings-and-restrictions/find-your-fire-weather-district"
