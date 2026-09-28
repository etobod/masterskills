---
name: loc-qa
description: Use when the user asks for a QA verdict on a plan or a change ("loc-qa", "loc-qa 018", "is plan 018 tested enough?"), and when loc-orchestrate has finished a plan's milestones. Runs the full test suite once, compares the tests with the plan's baseline copy, writes missing tests for the plan's criteria, runs the project's matching qa-* skills and ends with APPROVED or NOT APPROVED. Changes tests only.
argument-hint: "[plan <NNN> | <NNN>] [model]"
context: fork
agent: masterskills:qa
---

# loc-qa

A quality verdict for a plan: are its criteria really tested, did any test get weaker, does the whole suite pass? **Change test files only**: never production code, never `loc/TEST-PLAN.md`.

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

## 1. Scope

`$ARGUMENTS`:

- **`plan <NNN>` or `<NNN>`**: the plan in `loc/inbox/` or `loc/inbox/done/`, its state `loc/state/<NNN>.json`, its copy of the tests `loc/state/<NNN>/baseline/`. The QA file is `loc/state/<NNN>/qa.md`.
- **Nothing**: the plan whose state file has `phase: qa`; if none, the uncommitted changes, without plan checks; the QA file is `loc/state/qa-<YYYY-MM-DD>.md`.
- **`model`** anywhere: also run the model-behaviour layer (step 2).

Changed files, from the plan's first snapshot (`milestones[0].start`) or, without a plan, from `HEAD`:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/review_diff.py --from <start or HEAD> --out loc/state/<NNN>/qa.diff
```

Without a plan, `--out loc/state/qa.diff`.

Read `loc/TEST-PLAN.md` and the project's `CLAUDE.md` (`Commands`). No TEST-PLAN: the test command from `Commands` is the only layer, a gate.

## 2. Full suite, once

Each layer of TEST-PLAN section (a), in order:

- **gate** layer: run its command once. PASS or FAIL from the output. Missing command, a command that cannot start, or zero tests run: **SKIPPED** with the reason.
- **report** layer: run it; the result is **INFO**.
- **CI only**: do not run; **INFO** "CI only".
- **Model behaviour**: only with `model`; otherwise **SKIPPED** "not requested". When run, compare with the last line of `loc/state/qa-historia.log` and append one line: `<date> <plan or -> <layer> <result summary>`. Its result is **INFO**.

## 3. Tests against the copy

With a plan and a copy:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/test_baseline.py --plan <NNN> --compare
```

For each `changed` or `removed` file, compare it with `loc/state/<NNN>/baseline/files/<path>`. A removed or loosened assertion, a new skip or expected-failure marker, or a deleted test is **FAIL** unless a deviation in the state file or the plan's `## Rozstrzygnięcie` gives the reason. Added tests are fine. No copy: **INFO** "no baseline".

## 4. Criteria have tests

For every criterion ``- K<n>: … → `<test>` `` in the plan:

1. The named test exists and passed in step 2 → **PASS**.
2. It is missing → write it, following TEST-PLAN (e), and run it. At most 3 rounds for all missing tests together. It passes → **PASS** ("written by loc-qa"). It fails on its assertion → **FAIL**: the code does not meet the criterion; do not touch the code. Still broken after round 3 → **FAIL**.
3. `→ ręcznie` → **INFO** with the performer.

A milestone that changed code without `**Kryteria:**` → **INFO**. A gap in TEST-PLAN itself (section (b) says what to extend and nothing was) → an `odlozone` file, never an edit:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type odlozone --slug "<few words>" --title "<title>" --source "loc-qa <NNN>"
```

## 5. Project `qa-*` skills

Find `.claude/skills/qa-*/SKILL.md` in the project and read each header:

- has `qa-paths:` (a list of globs) and a changed file matches one → `Skill(skill: "<name>")` with the changed files that match. Its report decides **PASS** or **FAIL**.
- has `qa-paths:`, nothing matches → **INFO** "no matching changes".
- no `qa-paths:` → **INFO** "available, not run", plus once: "add `qa-paths:` to its header to run it automatically".

## 6. Verdict and QA file

**APPROVED** only when there is no FAIL and no SKIPPED gate layer. SKIPPED is allowed only in optional layers (report, model behaviour, CI only).

Write the QA file in Polish (the language of `loc/`):

```
# QA — plan <NNN>

**Werdykt:** APPROVED | NOT APPROVED
**Data:** <date "+%Y-%m-%d %H:%M">
**Zakres:** <from>..<to>, <n> zmienionych plików

| Sprawdzenie | Status | Dowód lub powód |
|---|---|---|
| warstwa jednostkowe: `python -m pytest -q` | PASS | `42 passed` |
| K2 → `tests/test_export.py::test_empty` | FAIL | `AssertionError: …` |
| qa-docs | INFO | dostępny, nie uruchomiony |
```

Then the rows for tests written by `loc-qa` (file and name) and new `odlozone` files.

## 7. Report

Return: the verdict, the QA file's path, each FAIL and SKIPPED with its reason, tests written, new inbox files. The caller records the `qa` gate; do not edit the state file.
