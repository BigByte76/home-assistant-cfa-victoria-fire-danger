# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Home Assistant custom integration, distributed through HACS, that reports CFA (Country Fire Authority, Victoria, Australia) fire danger ratings and Total Fire Ban status for today and tomorrow. Data comes from CFA's per-district RSS feeds, listed at https://www.cfa.vic.gov.au/rss-feeds. Domain: `cfa_victoria_fire_danger`. Follow the Home Assistant developer docs (https://developers.home-assistant.io/) and HACS publishing requirements.

## Commands

Uses `uv`. Tests need Python 3.14.2+, as required by `pytest-homeassistant-custom-component`; uv downloads it if needed. The test harness lags HA releases by a few weeks; use `/ha-live-test` for newer versions.

```sh
uv run --group test pytest                              # all tests
uv run --group test pytest tests/test_api.py::test_parse_central_feed  # one test
uv run --group lint ruff check --fix . && uv run --group lint ruff format .
```

Run `/ha-live-test <version>` (`.claude/skills/ha-live-test/`) to test on a real Home Assistant server, and `/release <version>` to cut a release. A PostToolUse hook (`.claude/hooks/post_edit.py`) runs ruff on edited Python files and blocks edits that make `strings.json` and `translations/en.json` differ.

CI (`.github/workflows/validate.yml`) runs hassfest, HACS validation, ruff and pytest.

## Architecture

Code is in `custom_components/cfa_victoria_fire_danger/`.

- `api.py`: feed client and parser. It has **no Home Assistant imports**, so keep it that way and test it directly. The feed URL is `https://www.cfa.vic.gov.au/cfa/rssfeed/{slug}-firedistrict_rss.xml`. Each `<item>` title is a date ("Thursday, 12 November 2026"). The item's HTML-escaped `<description>` holds the Total Fire Ban sentence ("… is not currently a day of Total Fire Ban"), a line `<District name>: <RATING>` and "forecast issued at: …". The feed mixes 12-hour and 24-hour time ("16:00 PM"). Undated items, such as municipal restrictions, are skipped. `parse_feed` returns `dict[date, DayForecast]`.
- `const.py`: `DISTRICTS` maps feed slug → district name. The name must exactly match the name in the feed text, because the rating line is matched against it. `RATINGS` holds the enum sensor options.
- `coordinator.py`: `CFACoordinator` polls every 15 minutes and wraps `CFAError` in a translated `UpdateFailed`. `CFAConfigEntry = ConfigEntry[CFACoordinator]` and the coordinator lives in `entry.runtime_data`. `async_track_day_rollover` calls `async_update_listeners()` just after each Melbourne midnight, because entities choose their day only when they write state.
- `entity.py`: base `CFAEntity` (a `CoordinatorEntity`) with a `day_offset`. It picks the forecast by **Melbourne local date** rather than feed position, and reports unavailable when the feed doesn't cover that day. `sensor.py` (enum rating, plus a numeric `level` attribute = index in `RATINGS`, so keep `RATINGS` in severity order) and `binary_sensor.py` (Total Fire Ban) are thin subclasses.
- `config_flow.py`: one step that validates the feed. The district slug is the config entry unique ID. Config entry **VERSION 2**. `async_migrate_entry` in `__init__.py` converts v1 entries, which stored the display name, to slugs.
- `brand/icon.png` and `icon@2x.png` are local brand images, shown by HA 2026.3+ and accepted by the HACS brands check. They were generated as an original flame; never use CFA or Home Assistant logos.
- Total Fire Ban detection: no archived feed (2022–2026) shows a declared-ban day, so `_is_total_fire_ban` treats any "day of Total Fire Ban" sentence without "not" as a ban. The verbatim sentence is exposed as the binary sensors' `statement` attribute so users can check it.
- Entity names, states, selector options and exception messages are translated. `strings.json` and `translations/en.json` must stay identical. Icons are in `icons.json`.
- Release: bump `version` in `manifest.json` and `pyproject.toml`, and add a `CHANGELOG.md` entry. `hacs.json` sets the minimum Home Assistant version (2026.2.3). CI tests that minimum by pinning `pytest-homeassistant-custom-component==0.13.316` (its release for HA 2026.2.3); update the pin when the minimum changes. Don't use APIs newer than the minimum.

`tests/fixtures/central.xml` is a real feed captured on 2026-11-12. Tests that check entity states freeze time to that date.
