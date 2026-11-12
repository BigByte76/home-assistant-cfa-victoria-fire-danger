"""End-to-end test of the integration on a real, throwaway Home Assistant server.

Installs a given Home Assistant version into a venv, starts it with this
integration symlinked in, then drives it over the REST API: onboarding,
config flow, entities, templates, duplicate check, diagnostics, brand icon,
v1 -> v2 migration, reload and removal. Fetches live CFA data.

Usage (from the repo root):
    python3 .claude/skills/ha-live-test/scripts/live_test.py --version 2026.11.1

Only standard library imports, so it runs with any Python 3.11+.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DOMAIN = "cfa_victoria_fire_danger"
RATINGS = {"no_rating", "moderate", "high", "extreme", "catastrophic"}
REPO = Path(__file__).resolve().parents[4]

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: object = "") -> bool:
    """Record and print one check."""
    results.append((ok, label))
    print(f"{'PASS' if ok else 'FAIL'}  {label}{f'  ({detail})' if detail else ''}")
    return ok


class HA:
    """Minimal REST client for a local Home Assistant."""

    def __init__(self, port: int) -> None:
        self.base = f"http://127.0.0.1:{port}"
        self.token: str | None = None

    def req(self, method: str, path: str, body=None, form: bool = False):
        headers = {}
        data = None
        if body is not None:
            if form:
                data = urllib.parse.urlencode(body).encode()
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                data = json.dumps(body).encode()
                headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                raw = resp.read()
                ctype = resp.headers.get_content_type()
                if ctype == "application/json" and raw:
                    return resp.status, json.loads(raw), ctype
                return resp.status, raw, ctype
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode(errors="replace"), ""

    def onboard(self) -> None:
        client_id = self.base + "/"
        status, res, _ = self.req(
            "POST",
            "/api/onboarding/users",
            {
                "client_id": client_id,
                "name": "Live test",
                "username": "livetest",
                "password": "live-test-password-1",
                "language": "en",
            },
        )
        if status != 200:
            sys.exit(f"Onboarding failed: {status} {res}")
        status, tok, _ = self.req(
            "POST",
            "/auth/token",
            {
                "grant_type": "authorization_code",
                "code": res["auth_code"],
                "client_id": client_id,
            },
            form=True,
        )
        if status != 200:
            sys.exit(f"Token exchange failed: {status} {tok}")
        self.token = tok["access_token"]

    def entries(self) -> list[dict]:
        _, data, _ = self.req(
            "GET", f"/api/config/config_entries/entry?domain={DOMAIN}"
        )
        return data if isinstance(data, list) else []

    def states(self, prefix: str) -> dict[str, dict]:
        _, data, _ = self.req("GET", "/api/states")
        return {
            s["entity_id"]: s
            for s in data
            if s["entity_id"].split(".", 1)[1].startswith(prefix)
        }

    def flow(self, district: str) -> dict:
        _, form, _ = self.req(
            "POST", "/api/config/config_entries/flow", {"handler": DOMAIN}
        )
        _, result, _ = self.req(
            "POST",
            f"/api/config/config_entries/flow/{form['flow_id']}",
            {"district": district},
        )
        return result


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def start(hass_bin: Path, config: Path, log: Path, ha: HA) -> subprocess.Popen:
    proc = subprocess.Popen(
        [str(hass_bin), "-c", str(config)],
        stdout=log.open("a"),
        stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            sys.exit(f"Home Assistant exited early; see {log}")
        try:
            urllib.request.urlopen(ha.base + "/api/onboarding", timeout=2)
            return proc
        except urllib.error.HTTPError:
            return proc
        except OSError:
            time.sleep(1)
    proc.terminate()
    sys.exit(f"Home Assistant did not start within 300 s; see {log}")


def stop(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        print("WARNING: Home Assistant did not stop within 60 s and was killed")


def wait_loaded(ha: HA, timeout: float = 120) -> list[dict]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        entries = ha.entries()
        if entries and all(
            e["state"] not in ("setup_in_progress", "not_loaded") for e in entries
        ):
            return entries
        time.sleep(1)
    return ha.entries()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--version", required=True, help="Home Assistant version, e.g. 2026.11.1"
    )
    parser.add_argument(
        "--python", default=">=3.14.2,<3.15", help="Python request passed to uv"
    )
    parser.add_argument("--port", type=int, default=18123)
    parser.add_argument("--district", default="central")
    args = parser.parse_args()

    work = REPO / ".ha-live" / args.version
    venv = work / "venv"
    config = work / "config"
    log = work / "home-assistant.log"
    hass_bin = venv / "bin" / "hass"

    if not hass_bin.exists():
        print(f"Installing Home Assistant {args.version} into {venv} ...")
        run(["uv", "venv", "-q", "--python", args.python, str(venv)])
        run(
            [
                "uv",
                "pip",
                "install",
                "-q",
                "--python",
                str(venv / "bin" / "python"),
                f"homeassistant=={args.version}",
            ]
        )

    shutil.rmtree(config, ignore_errors=True)
    (config / "custom_components").mkdir(parents=True)
    (config / "custom_components" / DOMAIN).symlink_to(
        REPO / "custom_components" / DOMAIN
    )
    (config / "configuration.yaml").write_text(
        "homeassistant:\n  name: CFA live test\n  time_zone: Australia/Melbourne\n  country: AU\n"
        f"http:\n  server_port: {args.port}\n"
        "api:\nonboarding:\nconfig:\ndiagnostics:\n"
        f"logger:\n  default: warning\n  logs:\n    custom_components.{DOMAIN}: debug\n"
    )
    log.write_text("")

    ha = HA(args.port)
    print(f"Starting Home Assistant {args.version} on port {args.port} ...")
    proc = start(hass_bin, config, log, ha)
    try:
        ha.onboard()
        _, cfg, _ = ha.req("GET", "/api/config")
        check(
            cfg.get("version") == args.version,
            "Running requested version",
            cfg.get("version"),
        )

        # Config flow and entities.
        result = ha.flow(args.district)
        check(
            result.get("type") == "create_entry",
            "Config flow creates entry",
            result.get("type"),
        )
        entries = wait_loaded(ha)
        check(
            bool(entries) and entries[0]["state"] == "loaded",
            "Entry loaded",
            entries and entries[0]["state"],
        )
        prefix = (
            f"cfa_{entries[0]['title'].lower().replace(' ', '_')}_"
            if entries
            else "cfa_"
        )
        states = ha.states(prefix)
        check(len(states) == 4, "Four entities created", sorted(states))
        for entity_id, state in states.items():
            attrs = state["attributes"]
            if entity_id.startswith("sensor."):
                check(
                    state["state"] in RATINGS,
                    f"{entity_id} has a rating",
                    state["state"],
                )
                check(
                    isinstance(attrs.get("level"), int),
                    f"{entity_id} has level",
                    attrs.get("level"),
                )
            else:
                check(
                    state["state"] in ("on", "off"),
                    f"{entity_id} is on/off",
                    state["state"],
                )
                check(
                    bool(attrs.get("statement")),
                    f"{entity_id} has statement",
                    attrs.get("statement"),
                )
            check(
                bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", attrs.get("date", ""))),
                f"{entity_id} has date",
                attrs.get("date"),
            )

        # The README's template.
        today = next(
            (e for e in states if e.startswith("sensor.") and e.endswith("_today")),
            None,
        )
        if today:
            status, rendered, _ = ha.req(
                "POST",
                "/api/template",
                {"template": f"{{{{ state_translated('{today}') }}}}"},
            )
            rendered = rendered.decode() if isinstance(rendered, bytes) else rendered
            check(
                status == 200 and rendered[:1].isupper(),
                "state_translated renders display name",
                rendered,
            )

        # Duplicate, diagnostics, brand icon.
        dup = ha.flow(args.district)
        check(
            dup.get("reason") == "already_configured",
            "Duplicate district rejected",
            dup.get("reason"),
        )
        # The diagnostics endpoint can 404 until that component finishes loading.
        deadline = time.monotonic() + 60
        while True:
            status, diag, _ = ha.req(
                "GET", f"/api/diagnostics/config_entry/{entries[0]['entry_id']}"
            )
            if status != 404 or time.monotonic() > deadline:
                break
            time.sleep(2)
        if status != 200:
            print(f"      diagnostics response: {str(diag)[:200]}")
        forecast = (
            diag.get("data", {}).get("forecast", []) if isinstance(diag, dict) else []
        )
        check(
            status == 200 and forecast and isinstance(forecast[0]["date"], str),
            "Diagnostics with plain dates",
            status,
        )
        if tuple(int(x) for x in re.findall(r"\d+", args.version)[:2]) >= (2026, 3):
            status, _, ctype = ha.req(
                "GET", f"/api/brands/integration/{DOMAIN}/icon.png"
            )
            check(
                status == 200 and ctype == "image/png",
                "Brand icon served",
                f"{status} {ctype}",
            )
        else:
            print("SKIP  Brand icon (local brand images need Home Assistant 2026.3+)")
        # Home Assistant saves config entries after a delay; wait for it.
        storage = config / ".storage" / "core.config_entries"
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline and not (
            storage.exists() and DOMAIN in storage.read_text()
        ):
            time.sleep(1)
    finally:
        stop(proc)

    # Migration: rewrite the entry in the v1 format. Acceptable only because
    # this is a throwaway instance; never edit .storage on a real one.
    if not check(storage.exists(), "Config entry saved to storage"):
        return 1
    data = json.loads(storage.read_text())
    for entry in data["data"]["entries"]:
        if entry["domain"] == DOMAIN:
            entry.update(
                version=1,
                minor_version=1,
                unique_id=None,
                title="CFA North Central",
                data={"district": "North Central"},
            )
    storage.write_text(json.dumps(data))

    print("Restarting with a v1 config entry ...")
    proc = start(hass_bin, config, log, ha)
    try:
        entries = wait_loaded(ha)
        check(
            bool(entries) and entries[0]["state"] == "loaded",
            "Migrated entry loaded",
            entries and entries[0]["state"],
        )
        # The migrated entry is saved after a delay, like any config entry change.
        deadline = time.monotonic() + 60
        while True:
            stored = json.loads(storage.read_text())
            migrated = [e for e in stored["data"]["entries"] if e["domain"] == DOMAIN]
            if (
                migrated and migrated[0]["version"] == 2
            ) or time.monotonic() > deadline:
                break
            time.sleep(1)
        check(
            bool(migrated)
            and migrated[0]["version"] == 2
            and migrated[0]["unique_id"] == "northcentral",
            "Entry migrated to v2",
            migrated and {k: migrated[0][k] for k in ("version", "unique_id")},
        )
        check(len(ha.states("cfa_north_central_")) == 4, "Migrated entities present")

        entry_id = entries[0]["entry_id"]
        status, _, _ = ha.req(
            "POST", f"/api/config/config_entries/entry/{entry_id}/reload"
        )
        check(
            status == 200 and wait_loaded(ha)[0]["state"] == "loaded", "Reload", status
        )
        status, _, _ = ha.req("DELETE", f"/api/config/config_entries/entry/{entry_id}")
        time.sleep(1)
        check(
            status == 200 and not ha.states("cfa_"),
            "Removal leaves no entities",
            status,
        )
    finally:
        stop(proc)

    problems = [
        line
        for line in log.read_text().splitlines()
        if DOMAIN in line
        and re.search(r"\b(WARNING|ERROR|CRITICAL)\b", line)
        and "has not been tested by Home Assistant" not in line
    ]
    check(not problems, "No integration warnings or errors in log", problems[:3])

    failed = [label for ok, label in results if not ok]
    print(
        f"\n{len(results) - len(failed)}/{len(results)} checks passed on Home Assistant {args.version}. Log: {log}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
