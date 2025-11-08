# CFA Victoria Fire Danger

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![License](https://img.shields.io/github/license/BigByte76/home-assistant-cfa-victoria-fire-danger)](LICENSE)
![GitHub last commit](https://img.shields.io/github/last-commit/BigByte76/home-assistant-cfa-victoria-fire-danger)

Custom Home Assistant integration that provides **Fire Danger Ratings** and **Total Fire Ban** information for **Victoria**, Australia — directly from CFA’s official RSS feeds.

## 🌦 Features
- Pulls data from the [CFA RSS feeds](https://www.cfa.vic.gov.au/rss-feeds)
- 15-minute update interval (matches CFA feed updates)
- Supports all CFA districts via dropdown menu
- Provides **today** and **tomorrow** fire danger ratings

## 🧩 Installation
1. Copy the `custom_components/cfa_victoria_fire_danger` folder into your Home Assistant `config/custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration → CFA Victoria Fire Danger**.
4. Choose your CFA District.

## 📊 Example Entities
- `sensor.cfa_fire_danger_today_central`
- `sensor.cfa_fire_danger_tomorrow_central`

## 📸 Screenshots
![screenshot](https://raw.githubusercontent.com/BigByte76/home-assistant-cfa-victoria-fire-danger/main/docs/screenshot.png)

## 🕒 Update Frequency
Updates every 15 minutes — the same as CFA RSS feed refresh cycle.

---
**Author:** [@BigByte76](https://github.com/BigByte76)
