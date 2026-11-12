"""Client for the CFA Victoria fire district RSS feeds.

This module has no Home Assistant dependencies so it can be tested in isolation.
Feeds are listed at https://www.cfa.vic.gov.au/rss-feeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import html
import re
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

import aiohttp

FEED_URL = "https://www.cfa.vic.gov.au/cfa/rssfeed/{slug}-firedistrict_rss.xml"
TIMEZONE = ZoneInfo("Australia/Melbourne")
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

_MONTHS = {
    name: index
    for index, name in enumerate(
        (
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ),
        start=1,
    )
}

# Item titles look like "Thursday, 12 November 2026".
_DATE_RE = re.compile(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})")
# "Bureau of Meteorology forecast issued at: Thursday, 12 November 2026 05:30 AM"
_ISSUED_RE = re.compile(
    r"issued at:\s*[A-Za-z]+,\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s+"
    r"(\d{1,2}):(\d{2})\s*([AP]M)?",
    re.IGNORECASE,
)
_TAG_BREAK_RE = re.compile(r"<\s*(?:br|/p)\s*/?\s*>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


class CFAError(Exception):
    """Base error for the CFA client."""


class CFAConnectionError(CFAError):
    """The feed could not be fetched."""


class CFAParseError(CFAError):
    """The feed could not be understood."""


@dataclass(frozen=True, slots=True)
class DayForecast:
    """Fire danger forecast for one district on one day."""

    date: date
    rating: str | None
    """Normalised rating, e.g. ``moderate`` or ``no_rating``."""
    total_fire_ban: bool | None
    total_fire_ban_statement: str | None
    """CFA's Total Fire Ban sentence for the day, verbatim."""
    issued_at: datetime | None


class CFAClient:
    """Fetches and parses CFA fire district feeds."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialise the client with a shared aiohttp session."""
        self._session = session

    async def async_get_forecast(
        self, slug: str, district_name: str
    ) -> dict[date, DayForecast]:
        """Return the forecast for a district, keyed by date."""
        url = FEED_URL.format(slug=slug)
        try:
            async with self._session.get(url, timeout=REQUEST_TIMEOUT) as resp:
                resp.raise_for_status()
                content = await resp.read()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CFAConnectionError(f"Error fetching {url}: {err}") from err
        return parse_feed(content, district_name)


def parse_feed(content: bytes, district_name: str) -> dict[date, DayForecast]:
    """Parse a fire district RSS feed into per-day forecasts."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as err:
        raise CFAParseError(f"Feed is not valid XML: {err}") from err

    days: dict[date, DayForecast] = {}
    for item in root.iter("item"):
        day = _parse_date(item.findtext("title") or "")
        if day is None:
            # Non-forecast items, e.g. "Fire restrictions by municipality".
            continue
        lines = _html_to_lines(item.findtext("description") or "")
        statement = _find_total_fire_ban_statement(lines)
        days[day] = DayForecast(
            date=day,
            rating=_parse_rating(lines, district_name),
            total_fire_ban=_is_total_fire_ban(statement),
            total_fire_ban_statement=statement,
            issued_at=_parse_issued_at(lines),
        )

    if not days:
        raise CFAParseError("Feed contained no forecast days")
    return days


def _html_to_lines(fragment: str) -> list[str]:
    text = html.unescape(_TAG_RE.sub("", _TAG_BREAK_RE.sub("\n", fragment)))
    return [line.strip() for line in text.splitlines() if line.strip()]


def _make_date(day: str, month: str, year: str) -> date | None:
    month_number = _MONTHS.get(month.lower())
    if month_number is None:
        return None
    try:
        return date(int(year), month_number, int(day))
    except ValueError:
        return None


def _parse_date(title: str) -> date | None:
    if (match := _DATE_RE.search(title)) is None:
        return None
    return _make_date(*match.groups())


def _parse_rating(lines: list[str], district_name: str) -> str | None:
    prefix = f"{district_name.lower()}:"
    for line in lines:
        if line.lower().startswith(prefix):
            value = line[len(prefix) :].strip()
            return re.sub(r"\W+", "_", value.lower()).strip("_") or None
    return None


def _find_total_fire_ban_statement(lines: list[str]) -> str | None:
    # e.g. "Today, Thu, 12 Nov 2026 is not currently a day of Total Fire Ban."
    # Every feed captured since 2022 uses this sentence. The footer line
    # "Displays when Total Fire Ban in force" does not match.
    for line in lines:
        if "day of total fire ban" in line.lower():
            return line
    return None


def _is_total_fire_ban(statement: str | None) -> bool | None:
    if statement is None:
        return None
    # No archived feed shows a declared ban, so a ban is inferred from the
    # absence of a negation in the statement.
    return re.search(r"\bnot\b", statement.lower()) is None


def _parse_issued_at(lines: list[str]) -> datetime | None:
    for line in lines:
        if (match := _ISSUED_RE.search(line)) is None:
            continue
        day, month, year, hour, minute, meridiem = match.groups()
        if (issued_date := _make_date(day, month, year)) is None:
            return None
        hour_value = int(hour)
        # The feed mixes 12h and 24h clocks, e.g. "16:00 PM".
        if meridiem and meridiem.upper() == "PM" and hour_value < 12:
            hour_value += 12
        elif meridiem and meridiem.upper() == "AM" and hour_value == 12:
            hour_value = 0
        try:
            return datetime(
                issued_date.year,
                issued_date.month,
                issued_date.day,
                hour_value,
                int(minute),
                tzinfo=TIMEZONE,
            )
        except ValueError:
            return None
    return None
