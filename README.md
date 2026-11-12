# CFA Victoria Fire Danger

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![Validate](https://github.com/BigByte76/home-assistant-cfa-victoria-fire-danger/actions/workflows/validate.yml/badge.svg)](https://github.com/BigByte76/home-assistant-cfa-victoria-fire-danger/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/BigByte76/home-assistant-cfa-victoria-fire-danger)](LICENSE)
![GitHub last commit](https://img.shields.io/github/last-commit/BigByte76/home-assistant-cfa-victoria-fire-danger)

A custom Home Assistant integration that shows **Fire Danger Ratings** and **Total Fire Bans** for the fire districts of **Victoria, Australia**. The data comes from the Country Fire Authority's (CFA) official [fire district RSS feeds](https://www.cfa.vic.gov.au/rss-feeds).

> [!IMPORTANT]
> **Upgrading from 0.x?** Version 2.0 is a rewrite. Your existing setup is migrated automatically, but entity IDs have changed. See the [changelog](CHANGELOG.md).

> [!WARNING]
> This is an unofficial integration and is not affiliated with or endorsed by CFA. Do not rely on it for safety decisions. Always check the [CFA website](https://www.cfa.vic.gov.au/) or [VicEmergency](https://emergency.vic.gov.au/) for official, current information.

## 🌦 Features
- Fire danger rating for **today** and **tomorrow**
- Total Fire Ban status for **today** and **tomorrow**
- All nine CFA fire districts. Add the integration once for each district you want
- Updates every 15 minutes
- "Today" and "tomorrow" use the date in Victoria, whatever time zone your Home Assistant uses
- Set up from the UI. No YAML needed

## 🧩 Installation
Requires Home Assistant **2026.2.3** or newer. Tested on 2026.2.3 and 2026.11.1. The integration icon appears in Home Assistant 2026.3 and later; on 2026.2.x the integration works but shows a placeholder icon.

### HACS (recommended)
[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=BigByte76&repository=home-assistant-cfa-victoria-fire-danger&category=integration)

1. In HACS, open the menu (⋮) → **Custom repositories**. Add `https://github.com/BigByte76/home-assistant-cfa-victoria-fire-danger` with the category **Integration**.
2. Search for **CFA Victoria Fire Danger** and download it.
3. Restart Home Assistant.

### Manual
1. Copy `custom_components/cfa_victoria_fire_danger` into the `custom_components` folder of your Home Assistant config directory.
2. Restart Home Assistant.

## ⚙️ Configuration
[![Open your Home Assistant instance and start setting up the integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=cfa_victoria_fire_danger)

1. Go to **Settings → Devices & services → Add integration**, then search for **CFA Victoria Fire Danger**.
2. Choose your fire district. If you're not sure which district you're in, use CFA's [find your fire district](https://www.cfa.vic.gov.au/warnings-and-restrictions/find-your-fire-weather-district) tool.

The district list includes Central, East Gippsland, Mallee, North Central, North East, Northern Country, South West, West and South Gippsland, and Wimmera.

## 📊 Entities
Each district is added as a device called `CFA <district>`. These are the entities for the Central district:

| Entity | Type | Description |
| --- | --- | --- |
| `sensor.cfa_central_fire_danger_rating_today` | Sensor | Today's fire danger rating |
| `sensor.cfa_central_fire_danger_rating_tomorrow` | Sensor | Tomorrow's fire danger rating |
| `binary_sensor.cfa_central_total_fire_ban_today` | Binary sensor | On when a Total Fire Ban is declared for today |
| `binary_sensor.cfa_central_total_fire_ban_tomorrow` | Binary sensor | On when a Total Fire Ban is declared for tomorrow |

### Fire danger rating states
The rating sensors use the [Australian Fire Danger Rating System](https://www.cfa.vic.gov.au/warnings-and-restrictions/fire-bans-ratings-and-restrictions/about-fire-danger-ratings) levels. In automations and templates, use the state value. The Home Assistant UI shows the display name.

| State value | Displayed as |
| --- | --- |
| `no_rating` | No rating |
| `moderate` | Moderate |
| `high` | High |
| `extreme` | Extreme |
| `catastrophic` | Catastrophic |

### Attributes
| Attribute | On | Description |
| --- | --- | --- |
| `date` | All entities | The date the forecast applies to |
| `issued_at` | All entities | When the Bureau of Meteorology issued the forecast |
| `statement` | Total Fire Ban entities | CFA's Total Fire Ban wording for the day, word for word |

An entity shows as **unavailable** if the CFA feed can't be reached, or if the feed doesn't include that day yet. This can happen for a few minutes after midnight.

## 🤖 Example automation
Send a notification at 7 pm when tomorrow is a Total Fire Ban day or the rating is Extreme or higher:

```yaml
automation:
  - alias: "Fire danger warning for tomorrow"
    triggers:
      - trigger: time
        at: "19:00:00"
    conditions:
      - condition: or
        conditions:
          - condition: state
            entity_id: binary_sensor.cfa_central_total_fire_ban_tomorrow
            state: "on"
          - condition: state
            entity_id: sensor.cfa_central_fire_danger_rating_tomorrow
            state:
              - extreme
              - catastrophic
    actions:
      - action: notify.notify
        data:
          title: "Fire danger tomorrow"
          message: >
            Rating: {{ states('sensor.cfa_central_fire_danger_rating_tomorrow') | replace('_', ' ') | title }}.
            {{ state_attr('binary_sensor.cfa_central_total_fire_ban_tomorrow', 'statement') }}
```

## 🛠 Troubleshooting
- **Download diagnostics:** go to **Settings → Devices & services → CFA Victoria Fire Danger**, then the ⋮ menu → **Download diagnostics**. Attach the file to bug reports.
- **Turn on debug logging:** add this to `configuration.yaml`:
  ```yaml
  logger:
    logs:
      custom_components.cfa_victoria_fire_danger: debug
  ```
- **Check a Total Fire Ban result:** the `statement` attribute shows CFA's original sentence. If it disagrees with the binary sensor's state, please [open an issue](https://github.com/BigByte76/home-assistant-cfa-victoria-fire-danger/issues) and include the statement.

## 🗑 Removal
1. Go to **Settings → Devices & services → CFA Victoria Fire Danger**. For each district, open the ⋮ menu and select **Delete**.
2. If you installed with HACS, remove the integration in HACS. If you installed manually, delete the `custom_components/cfa_victoria_fire_danger` folder.
3. Restart Home Assistant.

## 🧪 Development
You need [uv](https://docs.astral.sh/uv/). Tests run on Python 3.14.

```sh
uv run --group test pytest        # run the tests
uv run --group lint ruff check .  # lint
uv run --group lint ruff format . # format
```

On every push and pull request, GitHub Actions runs hassfest, HACS validation, ruff, and the tests against both the minimum supported (2026.2.3) and the latest Home Assistant.

## 📄 Data source
All data comes from the [Country Fire Authority](https://www.cfa.vic.gov.au/) through its public [RSS feeds](https://www.cfa.vic.gov.au/rss-feeds), subject to CFA's terms of use. Fire danger forecasts are issued by the Bureau of Meteorology.

---
**Author:** [@BigByte76](https://github.com/BigByte76) · Licensed under the [GNU GPL v3.0](LICENSE)
