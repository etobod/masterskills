# Tests in a plan

For every milestone that changes code. A milestone that changes only documents or configuration has no criteria: documents are not tested. It says so instead, with the reason: `**No tests:** tylko dokumenty`. `check_plan.py` rejects a milestone with neither line, so a plan never drops tests silently.

## What gets tested

1. The behaviour the plan changes: its acceptance criteria.
2. Regression: the whole suite still passes (`loc-qa` runs it once at the end).
3. Fixed contracts: the project's `qa-*` skills, run by `loc-qa`.
4. An explicit manual list, from `Manual verification / UAT` in `CLAUDE.md`.

## Acceptance criteria

The unit of testing is a criterion in a milestone, written as **what the code must do**, never "a test exists" or "it works":

```
**Criteria:**
- K1: `greet("Ann", "de")` returns `"Hallo, Ann"` → `test_app.py::test_german`
- K2 (behaviour): an unknown language gives the English greeting, no error → `test_app.py::test_unknown_language`
**Performer:** auto
**Proof:** `python -m unittest test_app` → `OK`
```

- Each criterion names its test in inline code: file and test name (`test_app.py::test_german`) or the id the framework runs directly (`test_app.TestGreet.test_german`). The test is assigned here and written **before** the code by `loc-orchestrate`.
- The milestone's proof is the test command and its expected result. It runs only the tests of this milestone's criteria plus the fast layers of `loc/TEST-PLAN.md` (a), **never the full suite**: the proof runs in every round of its gate, and `loc-qa` runs the full suite once at the end.
- Mark a criterion `(behaviour)` when it describes behaviour seen from outside (a user-visible result, an error path, a contract), not an internal detail. `loc-orchestrate` gives those to a separate test author who has not seen the implementation. Keep internal details unmarked.
- A test may be weakened later only openly, with the reason in the execution report. Say so in `## Risks and decisions` when a criterion is likely to change.

## The first plan with code

If the project has no test suite yet (no test command in `CLAUDE.md` `Commands`, no `loc/TEST-PLAN.md`), the plan starts with milestone **M1 — test suite**:

- the framework, the test directory and the command, added to `CLAUDE.md` `Commands`;
- one smoke test, proof: the command → `1 passed` (or the framework's equivalent);
- `loc/TEST-PLAN.md` copied from `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md`, with sections (a) layers and commands and (e) how a test looks here filled in. Write the path exactly so, never expanded: `check_plan.py` rejects the plugin's own path, since the plan must work on another machine. To see the template, read it at that path (the plugin's directory, the same one its scripts run from); do not search the disk for it.

No obvious framework (one HTML page, a script, "zero dependencies"): keep the logic in pure functions and test them with the language's built-in runner (`node --test`, `python -m unittest`); what can only be seen gets `**Performer:** user (…)`. A criterion's test is never a shell check (`grep`, `test -f`, `open`): those prove a word or a file exists, not behaviour, and `check_plan.py` rejects them.

Later milestones use that command in their proofs. `check_plan.py` rejects a plan with criteria when the project has no suite (`loc/TEST-PLAN.md` and a test command in `Commands`) and its M1 does not name `loc/TEST-PLAN.md`. M1 itself needs no `**Criteria:**`. Planning writes only the plan and inbox files: never create `loc/TEST-PLAN.md` or a test to satisfy the gate; M1 does that when it runs.

## `loc/TEST-PLAN.md`

It is the project's test contract and changes only through a milestone of a plan: when the plan adds something new to the product, one milestone extends section (b) "what changed → what to extend" (tests only). Never edit it on the side while doing something else. The test plan stays fixed otherwise.

## Performer and manual checks

`**Performer:**` says who proves the milestone:

- `auto` — the proof command, run by `loc-orchestrate` (the default);
- `agent` — a check an agent performs and records (e.g. reading a generated file against the criterion);
- `user (blocking)` or `user (deferrable)` — the user. The proof is the user's word with a date, recorded in the plan. A criterion may then point to `manual` instead of a test.

Use a manual milestone only when the proof cannot be a command. Each manual check has both flags: who performs it and whether it blocks.

- **Blocking**: stays in the plan; the plan is not done without it.
- **Deferrable**: becomes a `deferred` file in `loc/inbox/`. If an open `deferred` with manual checks already exists, append to it instead of creating another.

There is no separate manual-test document.

## Fixtures and recorded data

Fixtures committed to git are written by hand. Data recorded from real runs goes only to a directory the project ignores; name it in `loc/TEST-PLAN.md` section (e).
