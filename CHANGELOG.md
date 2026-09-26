# Changelog

All notable changes to the `masterskills` plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`.

## Unreleased

- `rules/core.md`: the always-loaded rules (12 points + 7a).
- `SessionStart` hook (startup, /clear, compaction): injects the rules and the project's open inbox; `scripts/py.sh` finds a working Python 3 on Windows and macOS.
- `scripts/inbox_summary.py`: open `inbox/` files and plan state files as JSON.
- `loc-init` skill and `scripts/init_project.py`: set up `inbox/`, `docs/` (PRD, PATTERNS, MEMORY), the `CLAUDE.md` sections and `tmp/` in `.gitignore`; idempotent, never overwrites, refuses a directory that is not a git root.
- `templates/`: the six inbox types, the three `docs/` files and the `CLAUDE.md` sections.
- `loc-brainstorm` skill: one growing brainstorm file in `inbox/` with numbered decisions (`B-01`…); records only.
- `loc-planning` skill: turns an inbox file, a PRD fragment or text into a plan with milestones and proofs, gated by `check_plan.py` and `rubber-duck` (at most 3 rounds, then `utknelo`); closes its input.
- `researcher` and `rubber-duck` agents (read-only).
- `scripts/next_number.py`: next inbox number, and creates an inbox file from its template with the time from the clock.
- `scripts/check_plan.py`: mechanical plan gate (sections, undecided phrases, placeholders, milestones = proofs).
- `loc-orchestrate` skill: executes a plan inline or with a sub-agent per milestone; a proof gate and a `code-review` gate per milestone (at most 3 rounds each, then `utknelo`), deviation rules 1–4, a closed list of stops, final `loc-review`, plan to `inbox/done/`, a proposed commit message and no commit.
- `loc-review` skill: `rubber-duck` and `code-review` in parallel with an explicit level (never `ultra`), project invariants and `❌` patterns; fixes the findings after a plan (at most 3 rounds), or reports to a `przeglad` file when run on its own.
- `scripts/check_state.py`: validates `tmp/state/<NNN>.json`, including the 3-round limit and its `utknelo` file.
- `scripts/snapshot.py`: a milestone snapshot as a dangling commit object (new files included), recorded in the state file; history, index and working tree stay untouched.
- `inbox_summary.py`: finished runs (`phase: done`) are no longer reported as active.

## 0.1.0 — 2026-09-26

- Plugin skeleton: manifest, standard directory layout.
- `scripts/measure.py`: enforces the word budget for rules, skills, references and agents.
- `scenarios/`: README and the first three behaviour scenarios.
