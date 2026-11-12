"""Claude Code PostToolUse hook: format and lint Python, keep translations in sync.

Reads the hook payload from stdin. Exit code 2 sends stderr back to Claude
so it can fix the problem.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
INTEGRATION = REPO / "custom_components" / "cfa_victoria_fire_danger"
STRINGS = INTEGRATION / "strings.json"
EN = INTEGRATION / "translations" / "en.json"


def main() -> int:
    """Run checks for the edited file."""
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    file_path = payload.get("tool_input", {}).get("file_path")
    if not file_path:
        return 0
    path = Path(file_path).resolve()
    if not path.is_relative_to(REPO) or not path.exists():
        return 0

    if path.suffix == ".py":
        subprocess.run(
            ["uv", "run", "-q", "--group", "lint", "ruff", "format", str(path)],
            cwd=REPO,
            capture_output=True,
            check=False,
        )
        lint = subprocess.run(
            ["uv", "run", "-q", "--group", "lint", "ruff", "check", "--fix", str(path)],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        if lint.returncode != 0:
            print(
                f"ruff found problems in {path.name}:\n{lint.stdout}", file=sys.stderr
            )
            return 2

    if path in (STRINGS, EN) and STRINGS.exists() and EN.exists():
        try:
            same = json.loads(STRINGS.read_text()) == json.loads(EN.read_text())
        except json.JSONDecodeError as err:
            print(f"{path.name} is not valid JSON: {err}", file=sys.stderr)
            return 2
        if not same:
            other = EN if path == STRINGS else STRINGS
            print(
                f"{path.relative_to(REPO)} and {other.relative_to(REPO)} differ. "
                "They must be identical; apply the same change to both.",
                file=sys.stderr,
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
