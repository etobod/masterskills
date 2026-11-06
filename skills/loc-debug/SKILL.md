---
name: loc-debug
description: Use when the user reports a bug outside a plan and wants it found and fixed (e.g. "loc-debug", "this doesn't work", "fix this bug", "why does it crash"). Reproduces it with a command, pins it with a failing test, tests hypotheses cheapest first and fixes the cause, not the symptom.
argument-hint: "[what goes wrong | error text | failing command]"
---

# loc-debug

A bug is fixed when a test that failed on it passes and nothing else broke. **Never fix on a guess**: a change made before the cause is shown hides the bug, it does not remove it.

Read first: the project's `CLAUDE.md` (`Commands`, `Invariants`), `loc/TEST-PLAN.md` (which layer catches what, how tests are written) and the entries of `loc/PATTERNS.md` whose **When to use** matches.

## 1. Reproduce

Get the bug as one command whose output shows it, e.g. `python -m pytest tests/test_export.py -k empty` → `KeyError: 'date'`, or a request with its wrong response. Use what the user gave (error text, steps, input); run it yourself. Note the exact command, input and output.

When it does not reproduce: say what you ran and what you saw, and ask the user one question for what is missing (the input, the environment, the exact steps), with an example of the answer you need. Do not go on without a reproduction.

A regression (it worked before): find the change that broke it with `git bisect run <the command>` when the command is quick, or by halving the input or the path through the code.

## 2. Failing test

Write the smallest test that fails **on this bug**, in the layer `loc/TEST-PLAN.md` names for it, the way section (e) says. Run it and see it fail on an assertion about the wrong behaviour, not on an import or a typo. A bug no test can reach (a device, the look of a page): the reproduction command from step 1 is the check, and say so.

## 3. Hypotheses

List two or three possible causes. For each, a check that tells it apart from the others: a value to print, a branch to force, an input to change, a line to read. Run the cheapest check first. A hypothesis is shown when its check gives the result it predicts and the others' do not.

Temporary logging and probe scripts go to `loc/tmp/` or are marked in the code so you can find them again; step 5 removes them all.

At most 3 rounds of hypotheses (rule 6). When a third round shows no cause, stop changing code: tell the user what was ruled out, with the checks and their results, and what is left; create a `deferred` file with the same, the reproduction and the failing test, so the work can be taken up later.

## 4. Fix the cause

Change the code where the cause is, not where the symptom shows: a missing `None` check at the crash hides a caller that should never pass `None`. The smallest change that makes the test pass; keep validation, error handling and the `Invariants`. Then run the failing test (it passes) and the project's fast suite from `CLAUDE.md` `Commands` (nothing else breaks).

When the right fix is larger than one change (a design flaw, several modules, a decision the user must make): fix nothing, and create a `deferred` file with the cause, the reproduction, the failing test and the fix you propose; `loc-planning` makes a plan from it.

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/py.sh" scripts/next_number.py --type deferred --slug "<bug, few words>" --title "<bug>" --source "loc-debug" --what "<cause, reproduction, failing test, proposed fix>" --why "<why it is larger than one change>" --when "the next loc-planning" --by loc-debug
```

Run each command on its own, exactly as written: no `cd`, variables, `;` or `&&`, so the plugin's permissions cover it.

## 5. Record

- A command that failed and another way that worked goes to `loc/PATTERNS.md` (rule 10).
- When the code changed: `Skill(skill: "masterskills:loc-journal", args: "<the bug, its cause, the fix and the test>")`.
- Remove the temporary logging and probes; `git status --short` shows only the fix and the test.

## 6. Report

Briefly, in the user's language: the reproduction, the cause with `file:line`, the fix, the test that now passes and the suite result; or, after 3 rounds, what was ruled out and the `deferred` file.
