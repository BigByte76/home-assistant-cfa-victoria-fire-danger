"""Tests for the CFA feed parser."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from custom_components.cfa_victoria_fire_danger.api import (
    TIMEZONE,
    CFAParseError,
    parse_feed,
)

from .conftest import load_fixture


def test_parse_central_feed() -> None:
    """The captured feed parses into five forecast days."""
    days = parse_feed(load_fixture("central.xml"), "Central")

    assert list(days) == [date(2026, 11, d) for d in range(12, 17)]
    today = days[date(2026, 11, 12)]
    assert today.rating == "moderate"
    assert today.total_fire_ban is False
    assert today.total_fire_ban_statement == (
        "Today, Thu, 12 Nov 2026 is not currently a day of Total Fire Ban."
    )
    assert today.issued_at == datetime(2026, 11, 12, 5, 30, tzinfo=TIMEZONE)

    tomorrow = days[date(2026, 11, 13)]
    assert tomorrow.rating == "no_rating"
    # The feed writes "16:00 PM"; this must not become 04:00.
    assert tomorrow.issued_at == datetime(2026, 11, 12, 16, 0, tzinfo=TIMEZONE)


def test_parse_total_fire_ban_declared() -> None:
    """A day without "not" in the Total Fire Ban sentence is a ban day."""
    feed = b"""<?xml version="1.0"?><rss><channel><item>
    <title>Saturday, 9 January 2027</title>
    <description>&lt;p&gt;Today, Sat, 9 Jan 2027 is a day of Total Fire Ban.&lt;/p&gt;
    &lt;p&gt;Mallee: EXTREME&lt;/p&gt;</description></item></channel></rss>"""

    day = parse_feed(feed, "Mallee")[date(2027, 1, 9)]

    assert day.total_fire_ban is True
    assert day.rating == "extreme"
    assert day.issued_at is None


def test_parse_missing_total_fire_ban_statement() -> None:
    """Unrecognised wording gives an unknown ban state, not a false negative."""
    feed = b"""<?xml version="1.0"?><rss><channel><item>
    <title>Saturday, 9 January 2027</title>
    <description>&lt;p&gt;Mallee: HIGH&lt;/p&gt;&lt;p&gt;Displays when Total Fire Ban
    in force&lt;/p&gt;</description></item></channel></rss>"""

    day = parse_feed(feed, "Mallee")[date(2027, 1, 9)]

    assert day.total_fire_ban is None
    assert day.total_fire_ban_statement is None


def test_parse_html_error_page() -> None:
    """An HTML page instead of XML raises a parse error."""
    with pytest.raises(CFAParseError):
        parse_feed(b"<html><body><p>Not found<br></p></body></html>", "Central")


def test_parse_feed_without_forecast_days() -> None:
    """A feed with no dated items raises a parse error."""
    feed = b"<rss><channel><item><title>Other</title></item></channel></rss>"
    with pytest.raises(CFAParseError):
        parse_feed(feed, "Central")
