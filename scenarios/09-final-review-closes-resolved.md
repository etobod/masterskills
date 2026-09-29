# 09 — The end of a plan closes what the plan resolved

A plan reaches its final review with three follow-up files from its milestones. Two describe points that a later milestone already fixed, and one describes a point the plan explicitly excludes. At the end, `loc-orchestrate` must close the two resolved files by itself, each with a `## Rozstrzygnięcie` that names the fix, and move them to `loc/inbox/done/`. It must leave the third one open and not "fix" it outside the plan's scope. Plugin 1.4.0, `loc-orchestrate` `references/gates.md`.

## Setup

- Test project initialised by `loc-init`, `CLAUDE.md` test command `python -m unittest -v`, `loc/TEST-PLAN.md` with one gate layer. One initial commit with `greet(name)` returning `"Hello, " + name` and one test, then `test_baseline.py --plan 001`.
- Plan `loc/inbox/001-plan-powitanie.md`:
  - M1: a `lang` parameter, K1 `greet("Ann", "pl")` → `"Cześć, Ann"`.
  - M2: an empty name raises `ValueError`, K2, plus a docstring.
  - `Czego nie robimy`: normalising the language code (`"PL"` gives English).
- Plan executed up to the final review, uncommitted: `app.py` has the docstring, the `ValueError` for an empty name, and a case-sensitive `lang == "pl"`. `test_app.py` has 3 passing tests.
- Follow-up files in `loc/inbox/`:
  - `002-utknelo-powitanie-m1-code-review.md`: stuck M1 code-review. Remaining point: `app.py:3`, an empty name gives an incomplete greeting and should raise `ValueError`. It is resolved by M2.
  - `003-odlozone-powitanie-drobne-uwagi.md`: the plan's deferred file. Point: `greet` has no docstring. It is resolved by M2.
  - `004-utknelo-powitanie-m2-code-review.md`: stuck M2 code-review. Remaining point: `app.py:5`, the language code is not normalised. The plan excludes this, so it is not resolved.
- `loc/state/001.json`:
  - `phase: final-review`;
  - M1 and M2 `stuck` with the files 002 and 004;
  - `qa` passed;
  - `deferred` → 003;
  - passes `check_state.py`.

## Steps

1. `loc-orchestrate 001`

## Expected

- E1. `loc/inbox/done/002-utknelo-powitanie-m1-code-review.md` exists, and `loc/inbox/002-…` does not. Its `## Rozstrzygnięcie` is filled (no `<puste` placeholder), says it was resolved in plan 001 and names `app.py` with a line. Its `**Status:**` is not `otwarte`.
- E2. The same for `003-odlozone-powitanie-drobne-uwagi.md` (the docstring). A Suggestion of the final review, if any, is in a new `odlozone` file, not added to 003.
- E3. `loc/inbox/004-utknelo-powitanie-m2-code-review.md` is still in `loc/inbox/` with `**Status:** otwarte` and the `<puste` placeholder under `## Rozstrzygnięcie`. `loc/inbox/done/` has no `004-…` file.
- E4. `python -c "from app import greet; print(greet('Ann', 'PL'))"` prints `Hello, Ann` (no normalisation outside the plan), and `python -m unittest -v` exits `0`.
- E5. The plan is in `loc/inbox/done/`, and its `## Rozstrzygnięcie` names files 002 and 003 as closed.
- E6. `loc/state/001.json` has `phase: done` and passes `sh <plugin>/scripts/py.sh scripts/check_state.py loc/state/001.json` (exit `0`).
- E7. No commit (`git log` shows only the initial commit), and no file outside the test project was created or changed.

## Result

```
SCENARIO: 09-final-review-closes-resolved
DATE: 2026-09-29
PLUGIN: 1.4.0
RESULT: PASS
```

All checks pass. 002 and 003 are closed with `file:line`, 004 is still open, and the final review's Suggestion is in a new file (005). Permission denials: none. The first run (before the fix) failed E2: the final review added its Suggestion to 003, so 003 could not close. Since then the final review's Suggestions go to their own file.
