# Changelog

All notable changes to the `masterskills` plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`.

## Unreleased

- `rules/core.md`: the always-loaded rules (12 points + 7a).
- `SessionStart` hook (startup, /clear, compaction): injects the rules and the project's open inbox; `hooks/run-hook.sh` finds a working Python 3 on Windows and macOS.
- `scripts/inbox_summary.py`: open `inbox/` files and plan state files as JSON.

## 0.1.0 — 2026-09-26

- Plugin skeleton: manifest, standard directory layout.
- `scripts/measure.py`: enforces the word budget for rules, skills, references and agents.
- `scenarios/`: README and the first three behaviour scenarios.
