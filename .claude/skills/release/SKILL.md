---
name: release
description: Prepare and publish a new version of the integration - bump versions, changelog, PR, then tag and GitHub release after merge.
argument-hint: "<version, e.g. 2.0.1>"
disable-model-invocation: true
---

# Release $ARGUMENTS

Stop and ask the user before each outward-facing step marked **(confirm)**.

## 1. Prepare on a branch
1. `git checkout main && git pull`, then `git checkout -b release/v$ARGUMENTS`.
2. Set the version to `$ARGUMENTS` in **both** `custom_components/cfa_victoria_fire_danger/manifest.json` (`version`) and `pyproject.toml` (`[project] version`). No `v` prefix in these files.
3. Add a `## $ARGUMENTS - <YYYY-MM-DD>` section at the top of `CHANGELOG.md` (below the title) with `Added` / `Fixed` / `Changed`, and `⚠️ Breaking changes` only if any. Write for users of the integration, not developers.
4. If the minimum Home Assistant version changed: update `hacs.json`, the README's "Requires Home Assistant" line, the CI matrix pin in `.github/workflows/validate.yml` (the `pytest-homeassistant-custom-component` release for that HA version), and CLAUDE.md.

## 2. Verify
- `uv run --group lint ruff check . && uv run --group lint ruff format --check .`
- `uv run --group test pytest`
- Run the `/ha-live-test` skill against the latest Home Assistant release.

## 3. Pull request (confirm)
Commit, push and open a PR with `gh pr create`. Watch `gh pr checks <n> --watch` and fix failures before going on. All five checks must pass (HACS, Hassfest, Lint, both Test jobs).

## 4. Merge and release (confirm)
1. Merge only when the user asks: `gh pr merge <n> --squash --delete-branch`, then `git checkout main && git pull`.
2. Check `main` has the new version: `grep '"version"' custom_components/cfa_victoria_fire_danger/manifest.json`.
3. Release notes = the new CHANGELOG section without its heading:
   `awk '/^## $ARGUMENTS/{f=1;next} /^## /{f=0} f' CHANGELOG.md > <scratch>/notes.md`
4. `gh release create v$ARGUMENTS --target "$(git rev-parse HEAD)" --title "v$ARGUMENTS" --notes-file <scratch>/notes.md --latest`
   `--target` needs the **full** SHA or a branch name; a short SHA is rejected.
5. Confirm: `gh api repos/{owner}/{repo}/releases/latest --jq .tag_name` prints `v$ARGUMENTS`.

HACS offers updates from GitHub releases, so a merged PR without a release does not reach users.
