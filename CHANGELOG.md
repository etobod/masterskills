# Changelog

All notable changes to the `masterskills` plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`.

## Unreleased

- `check_plan.py` rejects this plugin's own expanded path in a plan (a plan must work on another machine); `loc-planning/references/tests.md` requires `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md`. Scenario 05 checks it.

## 1.2.0 — 2026-09-28

- Tests in planning: a code milestone lists acceptance criteria (`**Kryteria:**`, ``- K<n>: <what the code must do> → `<test>` ``, `(zachowanie)` for behaviour seen from outside) and a performer (`**Wykonawca:** auto | agent | użytkownik (blokujący|odkładalny)`); `check_plan.py` enforces both. The first plan with code starts with a test-suite milestone. Details in `loc-planning/references/tests.md`.
- Template `templates/loc/TEST-PLAN.md` (the project's test contract, created by the first plan with code, not by `loc-init`) and a `## Project-specific workflow` section in the `CLAUDE.md` template.
- Scenario `05-first-plan-with-code`.
- Tests in plan execution (`loc-orchestrate/references/tests.md`): tests before code with a red gate `M<n>/red` that must fail on an assertion (its output kept in the state file, validated by `check_state.py`); a test written after its code proves itself by one hand-made mutation.
- `scripts/test_baseline.py`: a copy of the project's tests at the start of a plan (`loc/state/<NNN>/baseline/`), `--compare` lists changed, added and removed tests.
- `scripts/mutate.py` (`backup` / `restore`); the `SessionStart` hook restores a file left mutated by an interrupted session.
- Agent `test-author`: writes the tests for behaviour criteria before the code, without reading the implementation.
- Scenario `06-test-before-code`.
- Skill `loc-qa` (forked, runs as the `qa` agent): runs the full suite once, compares the tests with the plan's copy, writes missing tests for criteria, runs the project's `qa-*` skills whose `qa-paths:` match the change, and writes `loc/state/<NNN>/qa.md` with APPROVED or NOT APPROVED. Changes tests only.
- Agent `qa`.
- `loc-orchestrate`: a `qa` phase and gate before the final review for plans with `**Kryteria:**`; a plan whose QA gets stuck stays open. `check_state.py` rejects `journal` or `done` for such a plan without a passed or stuck `qa` gate.
- Scenarios `07-qa-paths-field` and `08-qa-no-tests-temptation`.
- A criterion may name its test by the id the framework runs directly (`test_app.TestGreet.test_polish`) as well as by file and test name.
- `PostToolUse` hook `after_push.py`: after a successful `git push` in a project with GitHub Actions workflows, one CI check with `gh run list`; a failed run becomes a `utknelo` inbox file. `plugin_commands.py` allows exactly that `gh run list` command.
- A `utknelo` file quotes the failure output of every round, also when it repeats the previous one (template and `loc-orchestrate`).
- README: the `loc/` workflow, `loc/TEST-PLAN.md`, `loc-qa` and the `test-author` agent.

## 1.1.0 — 2026-09-28

- All workflow files of a project live in `loc/`, ignored by git with one `.gitignore` line: `loc/inbox/`, `loc/PRD.md`, `loc/PATTERNS.md`, `loc/MEMORY.md`, plan state in `loc/state/`, review diffs in `loc/review/`, scratch files in `loc/tmp/`. `loc-init` no longer adds `tmp/` to `.gitignore` or `.gitkeep` files.
- Plans are closed with `mv` only: nothing in `loc/` is tracked.
- Templates moved to `templates/loc/`.
- Repeatable tests for the hooks and the `loc-init`/inbox scripts in `tests/` (`python -m unittest discover -s tests`).

## 1.0.1 — 2026-09-28

- `rules/core.md` rule 3: every inbox file is created with `next_number.py`, never by hand; rule 11 shortened to stay within the word budget.
- `SessionStart` context lists the inbox commands (`next_number.py` with the plugin path, `mv inbox/<file> inbox/done/`), to be run alone in the Bash tool so they need no approval.
- Scenario `04-question-in-conversation`: a question in plain conversation creates no file; a chat answer to a `pytanie` is recorded, moved to `inbox/done/` and becomes an `odlozone` file.

## 1.0.0 — 2026-09-26

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
- `scripts/memory_index.py`: keeps `docs/MEMORY.md` newest first, regenerates its index, trims to N entries (default 1000); adds an entry stamped with the clock; idempotent.
- `loc-journal` skill: one short diary entry per piece of work (`Plan`, `Przegląd`, `Poprawka`, `Decyzja`), corrects contradicted `PATTERNS.md` entries; never touches `docs/PRD.md`.
- `loc-orchestrate` calls `loc-journal` after closing the plan (`phase: journal`).
- `PreToolUse` hook `write_guard.py`: writes only inside the project, no exceptions; best-effort check of `Bash` and `PowerShell` redirections, `tee` and write cmdlets.
- `PreToolUse` hook `commit_guard.py`: denies `git commit` with AI attribution markers; ordinary mentions of AI pass.
- `loc-init` adds `.claude/settings.json` (`autoMemoryEnabled: false`, empty `attribution`), filling in only missing values (nested objects and lists included).
- `PreToolUse` hook `plugin_commands.py`: allows the skills' own commands (the plugin's scripts, `date +…`, moves from `inbox/` to `inbox/done/`) without a prompt; skills run each command on its own.
- `scripts/review_diff.py`: `loc-review` writes its diff through a script instead of a shell redirection.
- Scenario headings in English (`Setup`, `Steps`, `Expected`); results recorded under `## Result`.

## 0.1.0 — 2026-09-26

- Plugin skeleton: manifest, standard directory layout.
- `scripts/measure.py`: enforces the word budget for rules, skills, references and agents.
- `scenarios/`: README and the first three behaviour scenarios.
