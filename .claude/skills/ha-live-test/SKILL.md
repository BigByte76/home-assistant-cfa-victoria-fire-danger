---
name: ha-live-test
description: Test the integration end to end on a real, throwaway Home Assistant server of a given version, with live CFA data. Use when asked to test against a specific or the latest Home Assistant release, especially one newer than pytest-homeassistant-custom-component supports, or before a release.
argument-hint: "[version, e.g. 2026.11.1; default latest]"
---

# Live test on a real Home Assistant

The pytest suite runs on the HA version that `pytest-homeassistant-custom-component` is built for, which trails HA releases by a few weeks. This skill covers the gap by running the real `hass` binary.

## Steps

1. Choose the version. If `$ARGUMENTS` is empty, use the latest release:
   `curl -s https://pypi.org/pypi/homeassistant/json | python3 -c "import json,sys;print(json.load(sys.stdin)['info']['version'])"`
2. Run from the repo root (first run per version installs HA into `.ha-live/<version>/`, which takes a few minutes):
   `python3 .claude/skills/ha-live-test/scripts/live_test.py --version <version>`
   Options: `--python` (uv Python request, default `>=3.14.2,<3.15`), `--port` (default 18123), `--district` (default `central`).
3. Report the summary line (`N/M checks passed`) and every `FAIL` line with its detail. For a failure, read `.ha-live/<version>/home-assistant.log` before diagnosing.

## What it checks
Version running; config flow; four entities with valid states and `date`, `level` and `statement` attributes; the README's `state_translated` template; duplicate district rejected; diagnostics with plain dates; brand icon (2026.3+ only); v1 → v2 migration; reload; removal; no integration warnings or errors in the log.

## Notes
- It fetches live data from cfa.vic.gov.au, so rating values vary by day.
- The migration step edits `.storage/core.config_entries` of the throwaway instance only. Never do that on a real Home Assistant.
- HA saves config entries after a delay; the script waits for this. If a storage-based check fails, suspect timing first.
- Errors from unrelated core components (e.g. missing `ffmpeg`) are environment noise and are not counted.
