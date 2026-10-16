# Tests in a plan

For every milestone that changes code. A milestone that changes only documents or configuration has no criteria: documents are not tested. It says so instead, with the reason: `**Bez testów:** tylko dokumenty`. `check_plan.py` rejects a milestone with neither line, so a plan never drops tests silently.

## What gets tested

1. The behaviour the plan changes: its acceptance criteria.
2. Regression: the whole suite still passes (`loc-qa` runs it once at the end).
3. Fixed contracts: the project's `qa-*` skills, run by `loc-qa`.
4. An explicit manual list, from `Manual verification / UAT` in `CLAUDE.md`.

## Acceptance criteria

The unit of testing is a criterion in a milestone, written as **what the code must do**, never "a test exists" or "it works":

```
**Kryteria:**
- K1: `greet("Ann", "pl")` zwraca `"Cześć, Ann"` → `test_app.py::test_polish`
- K2 (zachowanie): nieznany język daje powitanie po angielsku, bez błędu → `test_app.py::test_unknown_language`
**Wykonawca:** auto
**Dowód:** `python -m unittest test_app` → `OK`
```

- Each criterion names its test in inline code: file and test name (`test_app.py::test_polish`) or the id the framework runs directly (`test_app.TestGreet.test_polish`). The test is assigned here and written **before** the code by `loc-orchestrate`.
- The milestone's proof is the test command and its expected result. It runs only the tests of this milestone's criteria plus the fast layers of `loc/TEST-PLAN.md` (a), **never the full suite**: the proof runs in every round of its gate, and `loc-qa` runs the full suite once at the end.
- Mark a criterion `(zachowanie)` when it describes behaviour seen from outside (a user-visible result, an error path, a contract), not an internal detail. `loc-orchestrate` gives those to a separate test author who has not seen the implementation. Keep internal details unmarked.
- A test may be weakened later only openly, with the reason in the execution report. Say so in `## Ryzyka i decyzje` when a criterion is likely to change.

## The first plan with code

If the project has no test suite yet (no test command in `CLAUDE.md` `Commands`, no `loc/TEST-PLAN.md`), the plan starts with milestone **M1 — zestaw testów**:

- the framework, the test directory and the command, added to `CLAUDE.md` `Commands`;
- one smoke test, proof: the command → `1 passed` (or the framework's equivalent);
- `loc/TEST-PLAN.md` copied from `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md`, with sections (a) layers and commands and (e) how a test looks here filled in. Write the path exactly so, never expanded: `check_plan.py` rejects the plugin's own path, since the plan must work on another machine. To see the template, read it at that path (the plugin's directory, the same one its scripts run from); do not search the disk for it.

Later milestones use that command in their proofs. `check_plan.py` rejects a plan with criteria for a project without `loc/TEST-PLAN.md` when its M1 does not name `loc/TEST-PLAN.md`. M1 itself needs no `**Kryteria:**`.

## `loc/TEST-PLAN.md`

It is the project's test contract and changes only through a milestone of a plan: when the plan adds something new to the product, one milestone extends section (b) "what changed → what to extend" (tests only). Never edit it on the side while doing something else. The test plan stays fixed otherwise.

## Performer and manual checks

`**Wykonawca:**` says who proves the milestone:

- `auto` — the proof command, run by `loc-orchestrate` (the default);
- `agent` — a check an agent performs and records (e.g. reading a generated file against the criterion);
- `użytkownik (blokujący)` or `użytkownik (odkładalny)` — the user. The proof is the user's word with a date, recorded in the plan. A criterion may then point to `ręcznie` instead of a test.

Use a manual milestone only when the proof cannot be a command. Each manual check has both flags: who performs it and whether it blocks.

- **Blocking** (`blokujący`): stays in the plan; the plan is not done without it.
- **Deferrable** (`odkładalny`): becomes an `odlozone` file in `loc/inbox/`. If an open `odlozone` with manual checks already exists, append to it instead of creating another.

There is no separate manual-test document.

## Fixtures and recorded data

Fixtures committed to git are written by hand. Data recorded from real runs goes only to a directory the project ignores; name it in `loc/TEST-PLAN.md` section (e).
