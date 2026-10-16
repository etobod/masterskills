# 09 — The end of a plan closes what the plan resolved

A plan reaches its final review with three follow-up files from its milestones. Two describe points that a later milestone already fixed, and one describes a point the plan explicitly excludes. At the end, `loc-orchestrate` must close the two resolved files by itself, each with a `## Resolution` that names the fix, and move them to `loc/inbox/done/`. It must leave the third one open and not "fix" it outside the plan's scope. Plugin 1.4.0, `loc-orchestrate` `references/gates.md`; E8 from 1.5.0 (the diary entry at the end of a plan); E2 and E9 from 1.6.0 (review notes in the plan).

## Setup

- Test project initialised by `loc-init`, `CLAUDE.md` test command `python -m unittest -v`, `loc/TEST-PLAN.md` with one gate layer. One initial commit with `greet(name)` returning `"Hello, " + name` and one test, then `test_baseline.py --plan 001`.
- Plan `loc/inbox/001-plan-powitanie.md`:
  - M1: a `lang` parameter, K1 `greet("Ann", "de")` → `"Hallo, Ann"`.
  - M2: an empty name raises `ValueError`, K2, plus a docstring.
  - `Out of scope`: normalising the language code (`"PL"` gives English).
  - `Not defended against`: `- none`.
- Plan executed up to the final review, uncommitted: `app.py` has the docstring, the `ValueError` for an empty name, and a case-sensitive `lang == "de"`. `test_app.py` has 3 passing tests.
- Follow-up files in `loc/inbox/`:
  - `002-stuck-powitanie-m1-code-review.md`: stuck M1 code-review, `**Category:** non-blocking`. Remaining point: `app.py:3`, an empty name gives an incomplete greeting and should raise `ValueError`. It is resolved by M2.
  - `003-deferred-powitanie-drobne-uwagi.md`: the plan's deferred file (a run started before 1.6). Point: `greet` has no docstring. It is resolved by M2.
  - `004-stuck-powitanie-m2-code-review.md`: stuck M2 code-review, `**Category:** non-blocking`. Remaining point: `app.py:5`, the language code is not normalised. The plan excludes this, so it is not resolved.
- `loc/state/001.json`:
  - `phase: final-review`;
  - M1 and M2 `stuck` with the files 002 and 004;
  - `qa` passed;
  - `deferred` → 003;
  - passes `check_state.py`.

## Steps

1. `loc-orchestrate 001`

## Expected

- E1. `loc/inbox/done/002-stuck-powitanie-m1-code-review.md` exists, and `loc/inbox/002-…` does not. Its `## Resolution` is filled (no `<empty` placeholder), says it was resolved in plan 001 and names `app.py` with a line. Its `**Status:**` is not `open`.
- E2. The same for `003-deferred-powitanie-drobne-uwagi.md` (the docstring). The final review creates no `deferred` file and adds nothing to 003: `loc/inbox/` and `loc/inbox/done/` have no `deferred` file other than 003. Its Suggestions and Unrealistic findings, if any, are lines in the plan's `## Review notes`.
- E3. `loc/inbox/004-stuck-powitanie-m2-code-review.md` is still in `loc/inbox/` with `**Status:** open` and the `<empty` placeholder under `## Resolution`. `loc/inbox/done/` has no `004-…` file.
- E4. `python -c "from app import greet; print(greet('Ann', 'PL'))"` prints `Hello, Ann` (no normalisation outside the plan), and `python -m unittest -v` exits `0`.
- E5. The plan is in `loc/inbox/done/`, and its `## Resolution` names files 002 and 003 as closed.
- E6. `loc/state/001.json` has `phase: done` and passes `sh <plugin>/scripts/py.sh scripts/check_state.py loc/state/001.json` (exit `0`).
- E7. No file outside the test project was created or changed.
- E8. `loc/MEMORY.md` has exactly one entry more than after setup: a `[Plan]` entry whose text ends with `Details: loc/inbox/done/001-plan-powitanie.md` and has at most 3 sentences before it. `loc/PATTERNS.md` is unchanged. The session transcript has no call of the `loc-journal` skill: `loc-orchestrate` writes the entry itself with one `memory_index.py` command.
- E9. If the plan has `## Review notes`, every non-blank line in it is `- suggestion (<gate>): …`, `- unrealistic (<gate>): … Who produces it: …` or `- enough (<gate>): … Reason: …` (E6's `check_state.py` checks this).

## Result

```
SCENARIO: 09-final-review-closes-resolved
DATE: 2026-09-29
PLUGIN: 1.6.0
RESULT: PASS
```

All checks pass. 002 and 003 are closed with `file:line`, 004 is still open, the plan names both closed files. E2: no new `deferred` file; the final review's one Suggestion is a line in the plan's `## Review notes` (E9, `check_state.py` exit `0`). E8: one new `[Plan]` entry by a single `memory_index.py` command, no `loc-journal` call, `loc/PATTERNS.md` unchanged. Permission denials: none. History: on 1.4.0 the first run failed E2 (the final review added its Suggestion to 003).
