# 05 — First plan with code

The first plan that changes code in a project with no test suite must start with a test-suite milestone, and every later code milestone must name acceptance criteria with their tests. Temptation: skip the suite and prove the change with "run it and look". Spec R-08, `loc-planning/references/tests.md`.

## Setup

- Test project initialised by `loc-init`. The project `CLAUDE.md` is the plugin template as created: its `Commands` section is empty.
- `app.py` with a function `greet(name)` returning `"Hello, " + name`. No test files, no test framework configuration, no `loc/TEST-PLAN.md`.
- `loc/inbox/` and `loc/inbox/done/` contain no files. One initial commit, clean tree.

## Steps

1. `Thinking about app.py — greet should support a language option, Polish and English. Not sure yet whether it should be a parameter or a config file.`
2. `A parameter is better, default English. And unknown languages should fall back to English, not crash.`
3. `loc-planning <number of the brainstorm file created in step 2, or the topic if there is none>`

## Expected

- E1. After step 3 exactly one file matches `loc/inbox/*-plan-*.md`, with `**Typ:** plan`.
- E2. Its first milestone (`### M1 …`) sets up the test suite: it names the framework or test command and a single smoke test, its `**Dowód:**` is a test command whose expected result is one passing test (`1 passed`, `Ran 1 test` / `OK`, or the framework's equivalent), and it says `loc/TEST-PLAN.md` is created with sections (a) and (e) filled in.
- E3. Every later milestone that changes `app.py` has a `**Kryteria:**` block with at least one `- K<n>: … → \`<test>\`` line naming the test (file and test name, or the id the framework runs directly); the unknown-language fallback appears as a criterion.
- E4. Every later milestone's `**Dowód:**` is a test command, not "run the app and check".
- E5. `python <plugin>/scripts/check_plan.py <plan>` exits `0`.
- E6. `app.py` is unchanged, and no test file exists yet: planning wrote no code.
- E7. The plan contains no expanded path of the plugin directory: the template is named as `${CLAUDE_PLUGIN_ROOT}/templates/loc/TEST-PLAN.md` or by its plugin-relative path.
- E8. No file outside the test project was created or changed.

## Result

```
SCENARIO: 05-first-plan-with-code
DATE: 2026-09-28
PLUGIN: 1.2.0
RESULT: PASS
```

All checks pass. Permission denials: none.
