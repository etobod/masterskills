# Changelog

All notable changes to the `masterskills` plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`.

## Unreleased

- `rules/core.md`: the always-loaded rules (12 points + 7a).
- `SessionStart` hook (startup, /clear, compaction): injects the rules and the project's open inbox; `scripts/py.sh` finds a working Python 3 on Windows and macOS.
- `scripts/inbox_summary.py`: open `inbox/` files and plan state files as JSON.
- `loc-init` skill and `scripts/init_project.py`: set up `inbox/`, `docs/` (PRD, PATTERNS, MEMORY), the `CLAUDE.md` sections and `tmp/` in `.gitignore`; idempotent, never overwrites, refuses a directory that is not a git root.
- `templates/`: the six inbox types, the three `docs/` files and the `CLAUDE.md` sections.

## 0.1.0 — 2026-09-26

- Plugin skeleton: manifest, standard directory layout.
- `scripts/measure.py`: enforces the word budget for rules, skills, references and agents.
- `scenarios/`: README and the first three behaviour scenarios.
