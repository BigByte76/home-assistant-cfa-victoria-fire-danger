# Changelog

## 2.0.0 - 2026-11-12

Version 2.0 is a rewrite. Earlier versions couldn't start: setup failed with `Error fetching data: not well-formed (invalid token)`.

### ⚠️ Breaking changes
- Home Assistant **2026.2.3** or newer is now required.
- Entity IDs and unique IDs have changed. For example, `sensor.cfa_fire_danger_today_central` is now `sensor.cfa_central_fire_danger_rating_today`. See the [README](README.md#-entities) for the full list. Update any dashboards and automations that use the old IDs.
- Rating sensor states are now fixed values: `no_rating`, `moderate`, `high`, `extreme` and `catastrophic`.

### Added
- **Total Fire Ban** binary sensors for today and tomorrow. Their `statement` attribute has CFA's own wording for the day.
- `date` and `issued_at` (Bureau of Meteorology forecast time) attributes on every entity.
- Each district is now a device, `CFA <district>`, linked to its CFA district page.
- Setup checks that the CFA feed can be reached, and stops you adding the same district twice.
- Diagnostics download, translated names and error messages, and icons that change with the state.
- An integration icon, shown in Home Assistant 2026.3 and later.
- A test suite, and CI that runs hassfest, HACS validation, ruff, and tests on both the minimum supported and the latest Home Assistant.

### Fixed
- Data now comes from CFA's real fire district feeds (`/cfa/rssfeed/<district>-firedistrict_rss.xml`). The old address returned an error page instead of a feed.
- Ratings are read from the right part of the feed. Earlier versions would have shown the date as the rating.
- "Today" and "tomorrow" use the date in Victoria instead of the order of items in the feed.
- Setup works on current Home Assistant releases. It had used a setup call Home Assistant has since removed.
- Entities update as soon as new data arrives.

### Changed
- Existing config entries are migrated automatically. You don't need to remove and re-add the integration.
- Removed the unused duplicate module `cfa_victoria_fire_danger.py`.
